# Building, validating, and running an MCAP import

Read this once your `.mcap` episodes are authored/converted/patched (see
[MCAP-AUTHORING.md](MCAP-AUTHORING.md) if not) and you're ready to build the
FiftyOne dataset and prove it's actually correct. If a tile isn't rendering
what you expect, see [MCAP-TROUBLESHOOTING.md](MCAP-TROUBLESHOOTING.md) instead.

## Contents

1. [Capability flags from schemas, not topic names](#capability-flags-from-schemas-not-topic-names)
2. [What goes on the sample vs. inside the MCAP](#what-goes-on-the-sample-vs-inside-the-mcap)
3. [Idempotency, collisions, and stale fields](#idempotency-collisions-and-stale-fields)
4. [Ambiguous or damaged episodes](#ambiguous-or-damaged-episodes-ship-variants-rather-than-silent-repairs)
5. [Temporal tags](#temporal-tags)
6. [Choosing which episodes to import](#choosing-which-episodes-to-import)
7. [Size, buffering speed, and cost](#size-buffering-speed-and-cost)
8. [Validation before declaring success](#validation-before-declaring-success)
9. [Non-negotiables](#non-negotiables)
10. [Process discipline](#process-discipline)
11. [Dataset case index](#dataset-case-index)
12. [The two companion docs to write per dataset](#the-two-companion-docs-to-write-per-dataset)

---

## Capability flags from schemas, not topic names

See [MCAP-TROUBLESHOOTING.md](MCAP-TROUBLESHOOTING.md#schema-to-tile-reference)
for the full schema-to-tile table this is derived from, matching the official
[Supported schemas](https://docs.voxel51.com/user_guide/multimodal.html#supported-schemas)
list. A topic's *name* is never a reliable signal for what it renders as.

```python
import os
import fiftyone as fo
from mcap.reader import make_reader

IMAGE_SCHEMAS = {"sensor_msgs/msg/Image", "sensor_msgs/msg/CompressedImage",
                 "foxglove.RawImage", "foxglove.CompressedImage", "foxglove.CompressedVideo"}
POINTCLOUD_SCHEMAS = {"sensor_msgs/msg/PointCloud2", "foxglove.PointCloud"}
# Other content that also renders in the 3D tile, but isn't a point cloud: laser
# scans, occupancy grids, poses/paths/transforms, markers, and 3D detections.
OTHER_3D_SCHEMAS = {"sensor_msgs/msg/LaserScan", "foxglove.LaserScan",
                    "nav_msgs/msg/OccupancyGrid", "foxglove.Grid",
                    "nav_msgs/msg/Odometry", "nav_msgs/msg/Path",
                    "geometry_msgs/msg/PoseStamped", "geometry_msgs/msg/PoseArray",
                    "foxglove.PoseInFrame", "visualization_msgs/msg/Marker",
                    "visualization_msgs/msg/MarkerArray", "foxglove.SceneUpdate",
                    "vision_msgs/msg/Detection3DArray"}
GPS_SCHEMAS = {"sensor_msgs/msg/NavSatFix", "foxglove.LocationFix"}
# sensor_msgs/msg/Imu isn't in the official supported-schemas list, but the Plot
# tile decodes any numeric field on any decodable topic, so it plots in practice.
IMU_SCHEMAS = {"sensor_msgs/msg/Imu"}
LOG_SCHEMAS = {"rosgraph_msgs/msg/Log", "rcl_interfaces/msg/Log", "foxglove.Log"}
TRANSFORM_SCHEMAS = {"tf2_msgs/msg/TFMessage", "geometry_msgs/msg/TransformStamped",
                     "foxglove.FrameTransform", "foxglove.FrameTransforms"}
KNOWN_SCHEMAS = (IMAGE_SCHEMAS | POINTCLOUD_SCHEMAS | OTHER_3D_SCHEMAS | GPS_SCHEMAS
                 | IMU_SCHEMAS | LOG_SCHEMAS | TRANSFORM_SCHEMAS)

def mcap_stats(path):
    with open(path, "rb") as f:
        summary = make_reader(f).get_summary()
        topics = sorted({c.topic for c in summary.channels.values()})
        schemas = sorted({summary.schemas[c.schema_id].name for c in summary.channels.values()
                          if c.schema_id in summary.schemas})
        stats = summary.statistics
        return {
            "topics": topics,
            "schemas": schemas,
            "message_count": stats.message_count,
            "channel_count": stats.channel_count,
            "duration_s": round((stats.message_end_time - stats.message_start_time) / 1e9, 1),
        }

def build_sample(mcap_path, **extra):
    stats = mcap_stats(mcap_path)
    schemas = set(stats["schemas"])
    return fo.Sample(
        filepath=mcap_path,
        duration_s=stats["duration_s"],
        message_count=stats["message_count"],
        channel_count=stats["channel_count"],
        topics=stats["topics"],
        schemas=stats["schemas"],
        has_image=bool(IMAGE_SCHEMAS & schemas),
        has_pointcloud=bool(POINTCLOUD_SCHEMAS & schemas),
        has_3d_content=bool((POINTCLOUD_SCHEMAS | OTHER_3D_SCHEMAS | TRANSFORM_SCHEMAS) & schemas),
        has_gps=bool(GPS_SCHEMAS & schemas),
        has_imu=bool(IMU_SCHEMAS & schemas),
        has_logs=bool(LOG_SCHEMAS & schemas),
        has_transforms=bool(TRANSFORM_SCHEMAS & schemas),
        has_unrecognized_schema=bool(schemas - KNOWN_SCHEMAS),
        **extra,
    )

dataset = fo.Dataset("my-dataset-multimodal", persistent=True)
dataset.add_samples([build_sample(p, scenario="urban") for p in episode_paths])
assert dataset.media_type == "multimodal", dataset.media_type
```

Add dataset-specific flags wherever they let you filter the grid, for example
`has_food_cam`, `has_2d_lidar_raw`, `has_ir`, `has_audio`, `has_gt_pose`,
`has_events`, `has_zed_dropout`.

Derive them from the file, not from the dataset's own metadata table. In one
import, an episode's CSV claimed a second camera was present but the bag had no
such topic at all. Keep the source column as a secondary cross-check field if it
is useful.

## What goes on the sample vs. inside the MCAP

- **Sample fields:** constants for the whole episode (ego velocity, distance to
  object, ambient temperature, scenario, operator, session, route length, GPS
  quality, degraded flags, ground-truth file paths). These are the only way to
  filter episodes in the grid without Enterprise MCAP indexing.
- **MCAP topics:** anything time-varying (telemetry, poses, per-frame labels).
- **`dataset.info`:** things shared by every episode, such as calibration
  matrices, source URL, license, paper reference, and excluded-sequence notes.

```python
dataset.info = {
    "source": "https://example.org/dataset",
    "license": "CC BY 4.0",
    "calibration": {"T_cam_lidar": {"R": R.tolist(), "t": t.tolist()}},
    "excluded_sequences": {"LF-03-D": "corrupted by a ~520ms backward clock step"},
}
dataset.save()
```

## Idempotency, collisions, and stale fields

```python
# refuse: safest for a one-shot import
if NAME in fo.list_datasets():
    raise SystemExit(f"Dataset '{NAME}' already exists; inspect or delete it first")

# add-only-what's-missing: right for incremental downloads
existing = {(s.sequence, s.variant) for s in dataset}
samples = [s for s in samples if (s.sequence, s.variant) not in existing]

# rebuild cleanly: right while the authoring code is still moving
if NAME in fo.list_datasets():
    fo.delete_dataset(NAME)
```

Datasets should be `persistent=True` unless you want them dropped when the
database session ends.

**Cached stats go stale.** After re-authoring an episode with different topics,
the sample's `message_count`, `channel_count`, `topics`, `schemas`, and `has_*`
fields do not refresh on their own, and a build script that refuses to re-run
will not update them. Re-read the MCAP and write the fields back:

```python
s = dataset.first()
stats = mcap_stats(s.filepath)
for k, v in stats.items():
    s[k] = v
s.save()
```

## Ambiguous or damaged episodes: ship variants rather than silent repairs

One sequence had a real 2.86 s camera dropout, and the release also shipped a
clean camera-only re-export on a third clock domain. Merging them would have
required re-timestamping across clock domains, which is real engineering rather
than an import-time decision (see
[MCAP-TROUBLESHOOTING.md §6](MCAP-TROUBLESHOOTING.md#6-timestamps-and-clock-domains)).
Both were imported as separate samples sharing `sequence="LF-02-N"`,
distinguished by `variant="original"` and `variant="svo_reexport"`, with an
honest `has_zed_dropout` flag.

## Temporal tags

`start` and `end` are nanoseconds elapsed since the start of the recording, as a
half-open interval `[start, end)`. This converts point-in-time markers into
intervals:

```python
import fiftyone.core.tags as fota

boundaries = [s["timestamp_ns"] - start_ns for s in subtasks] + [end_ns - start_ns]
for i, s in enumerate(subtasks):
    if boundaries[i + 1] > boundaries[i]:
        dataset.temporal_tags.add(
            fota.TemporalTag(sample_id, start=boundaries[i], end=boundaries[i + 1],
                             tag=s["task"]))

# query later
view = dataset.match_temporal_tags(tags="gripper closed")
```

Only tag from real event data, and verify the window falls inside the episode.

## Choosing which episodes to import

When a release has far more sequences than you can take, choose on content rather
than availability. One dataset had 303 candidate sequences that were all
file-identical in structure, so the selection criteria became GPS quality
(`RTK_fixed_cm`), no sensor dropout, not flagged degraded, low idle fraction, and
a spread across sessions and splits. State the rule so the sample is defensible.
See [Sample large corpora deliberately](#process-discipline) below for how this
scales to multi-terabyte corpora.

---

## Size, buffering speed, and cost

Ranked by measured impact across real imports:

1. **Raw uncompressed color images**, about 76 % of one scene's uncompressed
   bytes. JPEG transcode gives roughly 10x reduction — see
   [MCAP-TROUBLESHOOTING.md §5.8](MCAP-TROUBLESHOOTING.md#58-transcoding-raw-images-and-when-not-to).
2. **Derived accumulation or map topics**, about 55 % of one episode and the sole
   cause of a 201 GB blowup, while carrying zero unique information — see
   [MCAP-TROUBLESHOOTING.md §4.6](MCAP-TROUBLESHOOTING.md#46-accumulated-map-topics-and-how-they-blow-up-file-size).
3. **The highest-rate, highest-resolution lidar**, 74 % of one scene's payload
   after the image fix, from three stacked causes: 2x the other lidar's scan
   rate, 2x its angular resolution, and 2x wasted bytes per point.
4. **Full-resolution `32fc1` depth**, which alongside the point cloud dominates
   output size for a dense-ground-truth dataset.
5. **Per-point padding**, which halves uncompressed bytes and per-message decode
   cost but saves only about 5 % on disk after zstd — see
   [MCAP-TROUBLESHOOTING.md §4.3](MCAP-TROUBLESHOOTING.md#43-colour-fields-stride-and-packing).
6. **zstd level.** `MCAPWriteOptions(compression_level=19)` versus the SDK
   default of 0, which means "let zstd pick", typically 3. Still lossless, just
   more CPU per chunk:

   ```python
   from foxglove.mcap import MCAPWriteOptions
   with foxglove.open_mcap(path, allow_overwrite=True,
                           writer_options=MCAPWriteOptions(compression_level=19)):
       ...
   ```

Real cost figures from one 20-core NVMe machine, for a roughly 10-minute
multi-sensor car episode with video, lidar, dense depth, semantic, events, and
CAN:

| | Per 10 min episode |
|---|---|
| Source download, without the event stream | ~9.9 GB |
| Source download, with events | ~24 GB |
| Output MCAP | 9–14 GB |
| Conversion, 4 running in parallel | ~23 min each |

Conversion was largely single-core Python plus a multithreaded `ffmpeg`, measured
at about 2.5 cores per episode, so 4 jobs on 20 cores was comfortable and cut a
four-episode run from about 90 minutes serial to about 23.

Two process notes:

- Measure before optimizing. Both size investigations here started from "why does
  buffering take so long", sampled real per-topic message sizes with the `mcap`
  reader, and only then changed code.
- Mixing formats across episodes in one FiftyOne dataset is fine. Each MCAP is
  self-describing, so you don't have to re-author old episodes to adopt a new
  packing scheme.

**Downloading:** never pull a large Hub repo without a filter. One stray call
made while trying to list a 3,058-file repo put 17 GB of partial blobs in the
cache in about three minutes. Use an API listing call to enumerate, which
transfers nothing, and a download script that names its episodes explicitly —
see [HF-HUB-IMPORT.md](HF-HUB-IMPORT.md) for the general Hugging Face download
patterns this applies on top of.

---

## Validation before declaring success

### Summary read (footer only, no message decode)

Run `mcap_stats()` (above) on every input file and every file you produce. It
reads the footer, so it is nearly free even on a 25 GB file.

Sanity checks on the output:

- `duration_s` is close to the real recording length. A wildly inflated value
  means inconsistent timestamps across merged sources — see
  [MCAP-TROUBLESHOOTING.md §6.6](MCAP-TROUBLESHOOTING.md#66-rebasing-when-merging-sources).
- `message_count > 0` per file.
- Every schema either appears in
  [MCAP-TROUBLESHOOTING.md](MCAP-TROUBLESHOOTING.md#schema-to-tile-reference)'s
  decode table or is knowingly Message-tile only.

### A written file is not a good file

One episode out of eight came out of a parallel run **sparse**: 2.90 GB apparent,
1.45 GB allocated, with a 1.44 GB hole of zeros starting right after the first
chunk. Everything about it looked healthy from outside. The summary parsed,
statistics reported all 74,397 messages, and the chunk index was internally
consistent, indexing nothing inside the hole and simply jumping 1,445 MB between
two consecutive chunks. The App read a record length out of the zeros, got
1152921882580561845, and dropped the transform tree.

Nothing downstream noticed. The converter reported success, the builder ingested
the file, and the sample carried the right topics, message count, and channel
count, because all of that comes from the intact summary at the tail. **Only
opening the sample surfaced it.** This is the single most important reason tile
verification (below) is not optional, even when every automated check passes.

Two defences, both cheap:

```python
import os, struct

MCAP_MAGIC = b"\x89MCAP0\r\n"

def validate_mcap(path):
    """Raise unless every top-level record frames correctly and the file is fully
    written. Both checks are seek-bound: about 0.9 s to clear 47 GB, against ~80 s
    for a full message read of a single 13 GB file."""
    size = os.path.getsize(path)
    allocated = os.stat(path).st_blocks * 512
    if allocated < 0.95 * size:
        raise RuntimeError(f"{path}: sparse file, {allocated / 1e6:.0f} MB allocated "
                           f"of {size / 1e6:.0f} MB, content is missing")
    with open(path, "rb") as f:
        if f.read(8) != MCAP_MAGIC:
            raise RuntimeError(f"{path}: not an MCAP file")
        off = 8
        while off < size - 8:
            f.seek(off)
            header = f.read(9)
            if len(header) < 9:
                raise RuntimeError(f"{path}: truncated record header at {off}")
            opcode, length = header[0], struct.unpack("<Q", header[1:])[0]
            if not 1 <= opcode <= 15 or off + 9 + length > size:
                raise RuntimeError(f"{path}: bad record at offset {off}: "
                                   f"opcode {opcode}, length {length}")
            off += 9 + length
        if off != size - 8:
            raise RuntimeError(f"{path}: records end at {off}, expected {size - 8}")
        f.seek(off)
        if f.read(8) != MCAP_MAGIC:
            raise RuntimeError(f"{path}: missing trailing magic")
```

Either check alone would have caught that file. Run it at the end of every
conversion, before the file counts as done — and cheaply on every file you
*import* too, even if you didn't author it, since a corrupted download can look
identical to a healthy file until opened.

The second defence is process-level. Run parallel conversion pools under `spawn`
rather than the Linux default `fork`, so a worker never inherits the parent's
copy of the SDK's writer state:

```python
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

ctx = multiprocessing.get_context("spawn")
with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx) as pool:
    futures = {pool.submit(convert_one, job): job[0] for job in jobs}
    for future in as_completed(futures):
        record(*future.result())
```

The fault has not reproduced in a fresh single-job process, so treat it as an
intermittent fault in a forked pool and defend against it rather than explain it.

### Structural validation of an authored episode

Checks per-topic message counts against counts derived from the source files,
verifies related products agree, and asserts timestamps are ordered.

```python
from collections import defaultdict
from mcap.reader import make_reader

def verify(mcap_path, expected_counts):
    """expected_counts: {topic: n} derived from the SOURCE files, not the mcap."""
    ok = True
    with open(mcap_path, "rb") as f:
        reader = make_reader(f)
        summary = reader.get_summary()
        stats = summary.statistics

        per_topic = defaultdict(int)
        for cid, n in stats.channel_message_counts.items():
            per_topic[summary.channels[cid].topic] += n

        dur_s = (stats.message_end_time - stats.message_start_time) / 1e9
        print(f"{stats.message_count} msgs, {stats.channel_count} channels, {dur_s:.1f}s")

        for topic, want in expected_counts.items():
            got = per_topic.get(topic, 0)
            ok &= got == want
            print(f"  [{'OK ' if got == want else 'FAIL'}] {topic}: {got} (expected {want})")

        # per-channel monotonic log_time, and a full-scan count cross-check
        last_ts, non_monotonic, n_scanned = {}, defaultdict(int), 0
        for _s, channel, message in reader.iter_messages():
            n_scanned += 1
            prev = last_ts.get(channel.id)
            if prev is not None and message.log_time < prev:
                non_monotonic[channel.topic] += 1
            last_ts[channel.id] = message.log_time
        if non_monotonic:
            ok = False
            print(f"  [FAIL] non-monotonic log_time: {dict(non_monotonic)}")
        if n_scanned != stats.message_count:
            ok = False
            print(f"  [FAIL] scanned {n_scanned} != summary count {stats.message_count}")

    print(f"  => {'PASS' if ok else 'FAIL'}")
    return ok
```

Build `expected_counts` from the source data: the number of `.jpg` files in a
camera directory, rows in an IMU CSV, `.pcd` files, pose rows. Derived products
should agree with each other too, so if you emit a depth map, an overlay, and a
normal map per synced frame, all three counts must match, and a per-episode
calibration message should appear exactly once.

### Dataset-level checks

```python
dataset = fo.load_dataset(NAME)
assert dataset.media_type == "multimodal"
assert len(dataset) == expected_episode_count
for s in dataset:
    assert s.filepath.endswith(".mcap") and os.path.exists(s.filepath)
```

Report any mismatch with numbers. Do not declare success on a count you did not
check.

### Tile verification is a human step, and it is not optional

Nothing above proves a tile renders. Launching the App is the user's action:

```python
session = fo.launch_app(dataset)
```

Ask them to confirm, with the App open:

- the grid shows a stream preview per episode (the stream selector picks which);
- opening a sample and adding tiles produces real decoded data for each
  capability flag that was set;
- the 3D tile's reference frame is the tree root, and geometry is placed rather
  than sitting at the origin (see
  [MCAP-TROUBLESHOOTING.md §3.4](MCAP-TROUBLESHOOTING.md#34-reference-frames-tree-roots-and-disconnected-components));
- the timeline duration matches the sample's `duration_s`.

Before concluding a tile is broken, also check whether you're just early in
playback — many tiles legitimately show nothing until their topic's first
message ([MCAP-TROUBLESHOOTING.md §6.7](MCAP-TROUBLESHOOTING.md#67-real-gaps-that-look-like-bugs-but-arent)) —
and check [MCAP-TROUBLESHOOTING.md](MCAP-TROUBLESHOOTING.md#symptom--cause--fix-triage-table)
for the specific symptom before assuming a bug.

Some imports stop short of this step, and the honest thing to record is "not yet
visually verified in the App, don't assume the tiles were checked" — never
report success on the strength of a passing automated check alone.

---

## Non-negotiables

Read before writing any authoring or conversion code:

1. **One sample = one episode = one `.mcap` file.** The sample's `filepath` must
   end in `.mcap`, which is what sets `media_type == "multimodal"`.
2. **Inspect before you import, and validate everything you write.** The summary
   read is footer-only and nearly free. The structural check is seek-bound and
   clears 47 GB in about a second. A file that was written is not the same as a
   file that is good.
3. **Never fabricate data to make a tile render.** Omission is always allowed,
   invention never. Skip a zero-point scan rather than logging fake points; leave
   a camera frustum unplaceable rather than inventing extrinsics that were never
   recorded; fall back to greyscale-from-intensity rather than a made-up color.
4. **Verify calibration numerically against the data, not against the paper or
   the devkit.** Papers and devkits were wrong or self-contradictory in at least
   seven real datasets — see
   [MCAP-TROUBLESHOOTING.md §3.7](MCAP-TROUBLESHOOTING.md#37-frames-that-cannot-be-connected-and-conventions-that-bite).
5. **Prove one episode end-to-end in the App before batch-authoring the rest.**
   One import shipped 20 files before confirming a single one and had to redo
   them all.
6. **A working build is not a correct one.** Exit code 0 with plausible message
   counts held true at every stage of one multi-day debugging session, including
   the stages later found broken. Decoding real messages back out and checking
   actual values is what caught each bug.
7. **Derive capability flags from schema names, never topic-name substrings.** A
   topic called `/os_node/imu_packets` was a raw packet blob, not a decodable
   `Imu`. See [above](#capability-flags-from-schemas-not-topic-names).
8. **Write down what you verified, in the code.** Every non-obvious constant
   should carry the measurement that justifies it.

## Process discipline

1. **One episode, confirmed in the App, before the batch.** (Non-negotiable 5.)
2. **Treat the output path as a lock, and validate every file.** Two agent
   sessions independently started the same authoring script 18 s apart, both
   wrote the same output path, and the result was silent corruption with no
   error. `foxglove.open_mcap(..., allow_overwrite=True)` gives no protection
   against two writers racing on one path.
3. **Cheap re-authoring buys freedom.** One dataset could re-author all 36
   episodes in about 35 s, so three separate bugs were fixed without agonizing.
   Budget for this, because it changes which decisions are reversible.
4. **Write the numbers down in the code.** Every non-obvious constant should
   carry the measurement behind it: why a z-offset is -2.20, why a pitch is 0.0
   rather than the paper's 15°, why intensity is safe as `uint8`.
5. **Record what you deliberately did not do**, with the reason: an unfixable
   camera frustum, an unused second pose CSV, an excluded topic, a field whose
   semantics you could not confirm.
6. **Keep failed analyses as evidence.** The two scripts that failed to recover a
   radar's geometry are kept beside the one that succeeded, so their failure
   modes stay legible and nobody refits those constants a second time.
7. **Present judgment calls as explicit choices** with real numbers attached,
   rather than picking silently.
8. **Sample large corpora deliberately.** A 3.04 TB dataset was sampled as 20
   episodes stratified by size percentile per operator; an 8.94 TB dataset as the
   smallest full episode per task; a 9.4 TB dataset as one 30-second window per
   trajectory type.
9. **Cross-check the paper against the shipped files, both ways.** Real findings:
   a paper claiming per-image depth maps that exist in no sequence; a card
   quoting 2,203 episodes when 1,639 are uploaded; a documented 17-topic list
   when the bags carry 33; radar files with 3 more fields than documented; and a
   dataset with no bounding boxes at all despite the impression its description
   gives, verified against the full repo listing, the complete file tree, and the
   devkit.

## Dataset case index

Provenance for the findings across this skill's reference files, from real
imports of 16 robotics/AV datasets (ROS 1 bags, ROS 2 bags, Zarr and HDF5
exports, raw dumps of images, video, point clouds, radar, events, audio, GPS,
and IMU). These are internal dataset names — you never need to look them up —
listed so a lesson can be traced back to the import that produced it, and so a
future finding can be filed alongside the right one.

| Dataset | Path | Lessons it produced |
|---|---|---|
| `octosense` | C (HDF5 + video) | the 50 ms transform rule and untimestamped statics; H.264 encoder constraints; `mcap.calibration_topic`; camera geometry inference and the 0.5 px tolerance; depth encodings; JSON schema for Plot; uint8 colour; sparse-file corruption and `validate_mcap`; `spawn` pools; reading the viewer bundle; fitted radar constants |
| `grand_tour` | C (Zarr) | mixed static and dynamic chains failing to resolve; reference frame must be the tree root; disconnected coordinate roots; global time-span padding; Zarr chunk preloading; no `Imu` in foxglove-sdk; `Pose.position` needs `Vector3`; `JointStates`; `CompressedImage(format="png")` over `RawImage`; 16-bit depth pre-colorization; `kannala_brandt` Auto gap and the ImageAnnotations workaround; stale sample stats |
| `navwareset` | B (merge 2 ROS 1 bags) | topic and `frame_id` collisions; `CameraInfo` casing; static topic naming; planar-tf noise flattening; JPEG transcode; PointCloud2 repack; redundant-topic exclusion; devkit offset-convention math |
| `semanticspray` | C (author from raw) | one-shot transform expiry; skipping zero-point clouds; dropped class names; mount-height leakage in a "z" column; assumed-FPS timestamps; sample fields vs MCAP content |
| `yuto_mms` | C | 201 GB accumulation blowup and dry-run sizing; voxel prefix-slice trick; real RGB colorization; per-sequence calibration parsing; per-sequence timestamp conventions; concurrent-writer corruption; lossless `uint8` intensity; zstd 19 |
| `costnav_telepp` | A (patch existing) | ROS2-CDR PointCloud2 freeze vs foxglove.PointCloud; promoting rigid transforms to the static topic; byte-copy patch pattern; rosbag2 metadata bookkeeping; `CompressedImage.format` parsing; source-metadata vs file mismatch |
| `boreas` | C (devkit-driven) | GPS lat/lon in radians; era-dependent CSV columns; era-gated radar Doppler correction; box metadata via `KeyValuePair`; devkit-faithful box filtering; BEV footprint annotations |
| `oxford_spires` | C | topic tokens for geometry auto-detect; direct root-to-sensor transforms; PCL packed-rgb unpacking; field alignment and stride; fisheye calibration; the structural validation script |
| `canoe_dataset` | C (devkit-driven) | nearest-in-time sensor pairing; pre-baked lidar-on-camera overlay as its own JPEG topic; zero-return range filter; calibration logged once; CSV with a free-text header block |
| `fomo_dataset` | C | audio via `RawAudio`; polar and BEV radar images; static transforms from a transforms.json; arbitrary metadata CSVs as JSON channels; alpha-strip on PNG; ground truth recentered to a per-episode origin |
| `uosm_campus` | A | `log_time` vs `header.stamp` clock domains; dropout and re-export variants as separate samples; calibration in `dataset.info`; incremental add-only import |
| `xiangrui_rosbag2` | A (split) | splitting at a real mode signal; message-count conservation; 101 s startup dead zone; undecodable vendor schemas; documenting missing transforms and calibration rather than faking them |
| `hiw_500` | A | temporal tags from point markers; per-episode metadata and calibration sidecars; smallest-episode-per-task sampling |
| `maritime_lidar_scenarios` | A | ground-truth extrinsics as sample fields for a calibration benchmark; cross-checking MCAP topics against exported point-cloud folder counts |
| `msc_rad4r_dataset` | B | bag vs exploded-frames tradeoff, decided on timestamps; size-gated conversion script; download quota walls |
| `race16` | C (recon only) | color/depth index offset across shard boundaries; unconfirmed depth units; dummy all-zero IMU orientation; when a flat per-frame dataset may beat a single-episode one |

## The two companion docs to write per dataset

Worth reproducing for every dataset you import or author. Together they are what
makes an import reviewable, resumable by someone else, and traceable months
later — and are how the case index above and this whole skill got assembled in
the first place.

- **A recon doc** (facts): source, paper, license, download size; media table
  with modality, count, format, and verified details; a mapping table from source
  labels to FiftyOne or MCAP representations; other contents (splits, metadata,
  calibration, precomputed extras); structure recommendation with reasoning;
  numbered focus areas for import; and discrepancies between what the
  documentation claims and what the files contain.
- **An onboarding doc** (narrative): the architecture decision and why; decisions
  in order with reasoning; what actually made the import hard, with verified
  fixes rather than guesses; open questions and risks; a current-state table; key
  files; and a short "if you're picking this up cold" section.

Four rules for maintaining the onboarding doc:

- **Write down dead ends and their evidence.** A negative result that cost an
  hour is worth as much as a fix. A section explaining why some constants were
  fitted a particular way exists so nobody refits them a second time.
- **Record the number, not the impression.** "r = +0.13 against the depth ground
  truth" survives being read six months later. "The radar looked off" does not.
- **File it by kind.** Viewer behaviour goes in the symptom table
  ([MCAP-TROUBLESHOOTING.md](MCAP-TROUBLESHOOTING.md#symptom--cause--fix-triage-table)),
  source-data behaviour in the quirks list
  ([MCAP-AUTHORING.md §5](MCAP-AUTHORING.md#5-source-formats-zarr-hdf5-pcd-csv)),
  and anything that took a real investigation gets its own section.
- **Correct wrong entries in place rather than appending.** One radar was written
  up as effectively empty on the strength of one short episode; measurement later
  showed about 54,600 detections, so the original line was replaced, not
  annotated.

Keep the doc honest about what has not been verified. A line like "not yet
visually verified in the App, don't assume the tiles were checked" is what stops
the next person from treating an unfinished import as done.
