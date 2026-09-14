# Authoring, converting, merging, and patching MCAP files

Read this when your job is *producing* `.mcap` content — authoring fresh
episodes from raw data (Path C), converting ROS bags (Path B), or doing file
surgery (merge/split/patch) on files from any path. If your `.mcap` files
already exist and already render correctly, you don't need this file — see
[SKILL.md](SKILL.md)'s Step 9D instead. If something you authored isn't
rendering as expected, see [MCAP-TROUBLESHOOTING.md](MCAP-TROUBLESHOOTING.md).

## Contents

1. [The three paths, and the minimal authoring skeleton](#1-the-three-paths-and-the-minimal-authoring-skeleton)
2. [Authoring gaps in foxglove-sdk](#2-authoring-gaps-in-foxglove-sdk)
3. [Converting ROS bags](#3-converting-ros-bags)
4. [Merging, splitting, and patching MCAP files](#4-merging-splitting-and-patching-mcap-files)
5. [Source formats: Zarr, HDF5, PCD, CSV](#5-source-formats-zarr-hdf5-pcd-csv)
6. [Appendix A: complete ROS 1 two-bag merge](#appendix-a-complete-ros-1-two-bag-merge)
7. [Appendix B: complete MCAP patch tool](#appendix-b-complete-mcap-patch-tool)

---

## 1. The three paths, and the minimal authoring skeleton

| Path | Starting point | What you do |
|---|---|---|
| A | You already have `.mcap` files | Inspect, optionally patch or split, then build the dataset — this is [SKILL.md](SKILL.md)'s Step 9D job, not this file's |
| B | ROS 1 `.bag` or ROS 2 bags | Convert to one `.mcap` per episode, or hand-merge multiple bags — [§3](#3-converting-ros-bags) below |
| C | Raw sensor data (image folders, video, point clouds, Zarr, HDF5, CSV telemetry, GPS logs) | Author one `.mcap` per episode with `foxglove-sdk` — this section |

If a recording is split across multiple files (raw plus post-processed, or
time-chunked), merge them into a single `.mcap` per episode before importing —
see [§4](#4-merging-splitting-and-patching-mcap-files).

Four structural facts that drive everything else:

- Media type is inferred from the file extension. A sample whose `filepath` ends
  in `.mcap` makes the dataset `media_type == "multimodal"`. There is no importer
  class, no config, no media-type flag.
- One sample equals one episode. Don't split a recording into per-frame samples;
  the viewer handles playback within an episode. Nothing is unpacked to images on
  disk, since the viewer streams the MCAP.
- Media type is fixed per dataset. You cannot mix `.mcap` samples with plain
  images in one ungrouped dataset. Related non-MCAP media goes in its own dataset.
- Everything time-varying lives inside the MCAP as a topic. Everything constant
  for the whole episode lives as a FiftyOne sample field — see
  [MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#what-goes-on-the-sample-vs-inside-the-mcap).

### Minimal authoring skeleton

The smallest complete program that produces a valid multimodal episode with an
image stream, a point cloud, a GPS track, and numeric telemetry. Every other
technique in this skill is a modification of this shape.

```python
import foxglove
import numpy as np
from foxglove.channels import (
    CompressedImageChannel, PointCloudChannel, LocationFixChannel,
    FrameTransformChannel,
)
from foxglove.messages import (
    CompressedImage, PointCloud, LocationFix, FrameTransform,
    PackedElementField, PackedElementFieldNumericType, Timestamp, Vector3,
    Quaternion, Pose,
)

def ts(ns: int) -> Timestamp:
    """Every log_time is nanoseconds since the Unix epoch."""
    ns = int(ns)
    return Timestamp(sec=ns // 1_000_000_000, nsec=ns % 1_000_000_000)

f32 = PackedElementFieldNumericType.Float32
PC_FIELDS = [
    PackedElementField(name="x", offset=0, type=f32),
    PackedElementField(name="y", offset=4, type=f32),
    PackedElementField(name="z", offset=8, type=f32),
    PackedElementField(name="intensity", offset=12, type=f32),
]

cam_ch = CompressedImageChannel(
    topic="/cam_front/image_raw",                     # topic tokens matter, see MCAP-TROUBLESHOOTING.md#73
    metadata={"mcap.calibration_topic": "/cam_front/calibration"},   # see MCAP-TROUBLESHOOTING.md#72
)
lidar_ch = PointCloudChannel(topic="/lidar/points")
gps_ch = LocationFixChannel(topic="/gps")
tf_ch = FrameTransformChannel(topic="/tf")
static_tf_ch = FrameTransformChannel(topic="/tf_static")

with foxglove.open_mcap("episode_0001.mcap", allow_overwrite=True):
    # Rig extrinsics: log with NO timestamp, or they expire 50 ms into playback.
    # This is the single most common cause of "Missing transform" — see
    # MCAP-TROUBLESHOOTING.md#51.
    static_tf_ch.log(
        FrameTransform(
            parent_frame_id="base_link", child_frame_id="lidar",
            translation=Vector3(x=0.0, y=0.0, z=1.8),
            rotation=Quaternion(x=0.0, y=0.0, z=0.0, w=1.0),
        ),
        log_time=t0_ns,
    )

    for t_ns, jpeg_path in camera_frames:            # (capture_ns, path) pairs
        with open(jpeg_path, "rb") as f:
            cam_ch.log(
                CompressedImage(timestamp=ts(t_ns), frame_id="cam_front",
                                format="jpeg", data=f.read()),
                log_time=t_ns,
            )

    for t_ns, xyzi in lidar_sweeps:                  # xyzi: (N, 4) float32
        if xyzi.shape[0] == 0:
            continue                                 # never log an empty cloud, see MCAP-TROUBLESHOOTING.md#62
        lidar_ch.log(
            PointCloud(
                timestamp=ts(t_ns), frame_id="lidar",
                pose=Pose(position=Vector3(), orientation=Quaternion(w=1.0)),
                point_stride=16, fields=PC_FIELDS,
                data=np.ascontiguousarray(xyzi, dtype=np.float32).tobytes(),
            ),
            log_time=t_ns,
        )
        # The MOVING transform (world -> robot) is dynamic and must be re-logged
        # continuously, because a dynamic sample is only usable within 50 ms of
        # the playhead (MCAP-TROUBLESHOOTING.md#51).
        tf_ch.log(
            FrameTransform(
                timestamp=ts(t_ns), parent_frame_id="world", child_frame_id="base_link",
                translation=Vector3(x=px, y=py, z=pz),
                rotation=Quaternion(x=qx, y=qy, z=qz, w=qw),
            ),
            log_time=t_ns,
        )

    for t_ns, lat, lon, alt in gps_fixes:            # lat/lon in DEGREES, see MCAP-TROUBLESHOOTING.md#85
        gps_ch.log(
            LocationFix(timestamp=ts(t_ns), frame_id="gps",
                        latitude=lat, longitude=lon, altitude=alt),
            log_time=t_ns,
        )
```

Telemetry gets its own channel with a declared schema, which §2 explains:

```python
import json

def json_channel(topic, fields):
    """JSON telemetry channel with a declared schema so the Plot tile sees typed
    fields. `fields` maps name -> "number", "string", or "array"."""
    kinds = {"number": {"type": "number"},
             "string": {"type": "string"},
             "array": {"type": "array", "items": {"type": "number"}}}
    schema = foxglove.Schema(
        name=topic.strip("/").replace("/", "_"),
        encoding="jsonschema",
        data=json.dumps({"type": "object",
                         "properties": {n: kinds[k] for n, k in fields.items()}}).encode(),
    )
    return foxglove.Channel(topic, message_encoding="json", schema=schema)

telemetry_ch = json_channel("/telemetry", {"speed_mps": "number", "battery_pct": "number"})
for t_ns, speed, battery in telemetry_rows:
    telemetry_ch.log({"speed_mps": speed, "battery_pct": battery}, log_time=t_ns)
```

Rules baked into that skeleton:

- All streams in one episode must share a coherent time base. Episode duration is
  `max(log_time) - min(log_time)` across all channels.
- One channel object per topic, and a consistent `frame_id` per sensor.
- Use real capture timestamps, never wall-clock-at-conversion-time — see
  [MCAP-TROUBLESHOOTING.md §6](MCAP-TROUBLESHOOTING.md#6-timestamps-and-clock-domains).
- Newer SDK versions expose message types under `foxglove.messages`;
  `foxglove.schemas` is a deprecated alias that still works.
- Overlays/annotations (2D boxes, 3D cuboids, trajectories) are logged the same
  way — see [MCAP-TROUBLESHOOTING.md §5.9](MCAP-TROUBLESHOOTING.md#59-overlays-and-annotations).

## 2. Authoring gaps in `foxglove-sdk`

Decodable and authorable are different lists. What the viewer can *render* (see
[MCAP-TROUBLESHOOTING.md](MCAP-TROUBLESHOOTING.md)) is not the same as what the
SDK lets you *write*. Confirmed by inspecting `dir(foxglove.messages)` on 0.26.0:

- **There is no `Imu` message in `foxglove-sdk`.** The `Imu` in the decode table
  is the ROS schema, decoded when a bag already contains it. When authoring, log
  IMU as a JSON channel, which still populates the Plot tile through numeric
  field paths.
- **A JSON channel needs a declared schema to be plottable.** A channel created
  without one gets an auto-generated schema, and the Plot tile cannot offer its
  fields. Use the `json_channel()` helper above.
- **`Pose.position` needs a `Vector3`, not a `Point3`**, despite the docstring
  saying "Point denoting position". Passing `Point3` raises
  `TypeError: 'Point3' object is not an instance of 'Vector3'`. `Point3` is for
  `Point3InFrame` and standalone point fields.
- **`JointStates` / `JointState` exists** and is the right schema for per-joint
  kinematic arrays (position, velocity, effort, acceleration). It is far more
  compact than flattening 12 joints into a JSON dict, and gets proper binary
  encoding.
- **`CompressedImage.format` accepts `png`, not only `jpeg`.** For any image
  already on disk, prefer re-encoding to `CompressedImage` over `RawImage`, even
  for single-channel masks. Logging one camera's masks as full-resolution
  `RawImage` mono8 would have been about 8.3 GB, against about 27 MB for the same
  content as PNG.

## 3. Converting ROS bags

### 3.1 Straight conversion

```bash
rosbags-convert --src episode.bag --dst episode_out --dst-storage mcap \
                --compress zstd --compress-mode storage
```

- `--dst` is a directory in rosbag2 layout. The actual file is
  `episode_out/episode_out.mcap`, and that is what the sample points at.
- Filter channels with `--exclude-topic`, `--include-topic`, `--exclude-msgtype`,
  `--include-msgtype`. Exclusions win.
- If a ROS 2 bag already uses mcap storage, the `.mcap` inside can be used
  directly. Inspect it first — see
  [MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#summary-read-footer-only-no-message-decode).

Gate conversion on a completeness check so a truncated download can't be
converted silently:

```bash
TARGET_BYTES=10906820379
ACTUAL_BYTES=$(stat -c%s episode.bag)
if [ "$ACTUAL_BYTES" -lt "$TARGET_BYTES" ]; then
  echo "incomplete: ${ACTUAL_BYTES} / ${TARGET_BYTES} bytes. Not converting."
  exit 1
fi
```

### 3.2 ROS 1 to ROS 2 CDR by hand: two typestores, always

Needed when a plain conversion can't intercept messages, which is the case for
topic remapping, frame remapping, transcoding, or merging two bags.

```python
from rosbags.convert.converter import get_types_from_msg
from rosbags.typesys import Stores, get_typestore

def build_typestores(*readers):
    """Two stores, not one. Deserializing raw ROS 1 bytes needs the genuine ROS 1
    Header (which has `seq`); serializing ROS 2 CDR needs the Header without it.
    Sharing one store misaligns every message with a nested Header."""
    src_store = get_typestore(Stores.EMPTY)   # deserialize_ros1
    dst_store = get_typestore(Stores.EMPTY)   # serialize_cdr / generate_msgdef
    foxy = get_typestore(Stores.ROS2_FOXY)
    dst_store.register({"std_msgs/msg/Header": foxy.FIELDDEFS["std_msgs/msg/Header"]})

    camerainfo_def = {"sensor_msgs/msg/CameraInfo": foxy.FIELDDEFS["sensor_msgs/msg/CameraInfo"]}
    src_store.register(dict(camerainfo_def))          # see MCAP-TROUBLESHOOTING.md#71
    dst_store.register(dict(camerainfo_def))
    dst_store.register(                                # output-only type for transcoding
        {"sensor_msgs/msg/CompressedImage": foxy.FIELDDEFS["sensor_msgs/msg/CompressedImage"]}
    )

    for reader in readers:
        for conn in reader.connections:
            msgtype = resolve_msgtype(conn.msgtype)
            typs = get_types_from_msg(conn.msgdef, conn.msgtype)
            if conn.msgtype != msgtype:
                typs[msgtype] = typs.pop(conn.msgtype)
            typs.pop("sensor_msgs/msg/CameraInfo", None)
            src_store.register(dict(typs))
            typs.pop("std_msgs/msg/Header", None)
            dst_store.register(typs)
    return src_store, dst_store
```

Write schemas with `encoding="ros2msg"` and
`dst_store.generate_msgdef(msgtype, ros_version=2)`, and channels with
`message_encoding="cdr"`. That is what the viewer decodes.

### 3.3 Legacy msgtype aliases

A ROS 1 bag can carry a canonical type under an old name. In one real bag, one of
four `/tf` connections was typed `tf/tfMessage` (12,485 messages) while the other
three were `tf2_msgs/msg/TFMessage`. They are structurally identical. Unaliased,
the legacy connection forks into a second channel under the same topic, and every
`.endswith("TFMessage")` check skips it.

```python
MSGTYPE_ALIASES = {"tf/tfMessage": "tf2_msgs/msg/TFMessage",
                   "tf/msg/tfMessage": "tf2_msgs/msg/TFMessage"}

def resolve_msgtype(msgtype):
    return MSGTYPE_ALIASES.get(msgtype, msgtype)
```

Key schemas and channels by the resolved msgtype, never the raw one.

## 4. Merging, splitting, and patching MCAP files

### 4.1 Merging N already-written MCAPs

Schema and channel IDs are per-file, so re-register them against the output
writer, deduped by `(encoding, name)` and `(topic, message_encoding)`. This merges
files with different encodings, for example a ROS2/CDR conversion and a
Foxglove/protobuf annotations file, into one episode.

```python
import heapq
from pathlib import Path
from mcap.reader import make_reader
from mcap.writer import Writer as McapWriter

def merge_mcaps(srcs: list[Path], dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    readers = [make_reader(open(s, "rb")) for s in srcs]

    with open(dst, "wb") as out:
        writer = McapWriter(out)
        writer.start()
        schema_id_map, channel_id_map = {}, {}

        def gen(reader):
            for schema, channel, message in reader.iter_messages():
                skey = (schema.encoding, schema.name) if schema else None
                if skey is not None and skey not in schema_id_map:
                    schema_id_map[skey] = writer.register_schema(
                        name=schema.name, encoding=schema.encoding, data=schema.data)
                ckey = (channel.topic, channel.message_encoding)
                if ckey not in channel_id_map:
                    channel_id_map[ckey] = writer.register_channel(
                        topic=channel.topic, message_encoding=channel.message_encoding,
                        schema_id=schema_id_map[skey] if skey is not None else 0)
                yield message.log_time, channel_id_map[ckey], message

        n, first_ts, last_ts = 0, None, None
        for log_time, channel_id, message in heapq.merge(
            *[gen(r) for r in readers], key=lambda x: x[0]
        ):
            writer.add_message(channel_id, log_time=message.log_time,
                               data=message.data, publish_time=message.publish_time)
            first_ts = log_time if first_ts is None else min(first_ts, log_time)
            last_ts = log_time if last_ts is None else max(last_ts, log_time)
            n += 1
        writer.finish()
    print(f"merged {len(srcs)} files, {n} messages, span {(last_ts - first_ts)/1e9:.2f}s")
```

### 4.2 Patching an existing MCAP without re-authoring it

The right tool whenever you need to add or fix one topic in a big file. Full
implementation in [Appendix B](#appendix-b-complete-mcap-patch-tool). The rules
that make it safe:

1. Copy every schema and channel to a new writer, keeping ID maps.
2. Copy every message byte-for-byte (`data`, `log_time`, `publish_time`,
   `sequence`). No decode, no re-encode, no risk.
3. Insert your new messages at the right `log_time`.
4. **Update the embedded rosbag2 metadata record.** ROS 2 bags carry a `rosbag2`
   metadata record holding `topics_with_message_count`. If you add messages and
   don't update it, `ros2 bag info`-style consumers report stale counts. FiftyOne
   reads topics from MCAP channel and schema records directly, so this is
   cosmetic for the viewer but wrong to leave inconsistent.
5. **Do not fabricate a metadata entry for a Foxglove-schema topic you spliced
   in.** It isn't a native ROS 2 bag topic, and giving it a
   `serialization_format: cdr` entry reintroduces exactly the type and format
   inconsistency that caused an earlier bug.

### 4.3 Splitting one long recording into episodes

Split at semantically meaningful boundaries rather than arbitrary equal chunks.
One recording published its own operating mode on a string topic, so every real
mode switch became an episode boundary. Present the candidate segmentations with
exact timings and message counts and let the user choose.

```python
from pathlib import Path
from mcap.reader import make_reader
from mcap.writer import CompressionType, Writer

def split(src: Path, out_dir: Path, episodes, bag_start_ns: int):
    """episodes: list of (filename, start_offset_s, end_offset_s)."""
    out_dir.mkdir(exist_ok=True)
    with open(src, "rb") as f:
        reader = make_reader(f)
        summary = reader.get_summary()

        for name, start_off, end_off in episodes:
            start_ns = bag_start_ns + int(start_off * 1e9)
            end_ns = bag_start_ns + int(end_off * 1e9)
            with open(out_dir / name, "wb") as out_f:
                writer = Writer(out_f, compression=CompressionType.ZSTD)
                writer.start()
                schema_id_map = {
                    sid: writer.register_schema(name=s.name, encoding=s.encoding, data=s.data)
                    for sid, s in summary.schemas.items()
                }
                channel_id_map = {
                    cid: writer.register_channel(
                        topic=c.topic, message_encoding=c.message_encoding,
                        schema_id=schema_id_map.get(c.schema_id, 0), metadata=c.metadata)
                    for cid, c in summary.channels.items()
                }
                count = 0
                for _schema, channel, message in reader.iter_messages(
                    start_time=start_ns, end_time=end_ns
                ):
                    writer.add_message(
                        channel_id=channel_id_map[channel.id], log_time=message.log_time,
                        data=message.data, publish_time=message.publish_time,
                        sequence=message.sequence)
                    count += 1
                writer.finish()
            print(f"{name}: {count} msgs, [{start_off:.1f}s, {end_off:.1f}s)")
```

Always verify conservation. In the split that produced this code, the 5 output
files summed to exactly 53,219 messages, the source's total.

Keep genuinely odd episodes rather than merging them away, and explain them in a
sample field. One 12.3 s episode was almost entirely a system-load burst window,
kept for fidelity to the mode signal with the caveat recorded.

### 4.4 Dropping redundant topics

One merge excludes a single topic: a dense pre-fused XYZRGB `PointCloud2` that
the robot's own node derived from the depth image, RGB image, and camera info,
all three of which are kept. It measured 11.18 GB, 57 % of the episode's raw
content, and was the single largest topic.

The exclusion criterion was *provably derivable from other retained topics*, not
merely large. Document what is lost.

## 5. Source formats: Zarr, HDF5, PCD, CSV

Gotchas that cost real time before a single message was written.

### 5.1 Zarr

- **Preload every array with `[:]` before indexing it in a loop.** Some arrays
  are stored as a single chunk covering the whole array, so `arr[i]` inside a
  Python loop re-decompresses the entire chunk on every access. This alone turned
  a 1-minute build into a 27-minute hang. Do `x = group["field"][:]` once, then
  index the numpy array.
- **A malformed root group can block the whole store.** One mission's root
  `.zgroup` was 24 bytes of truncated JSON declaring `zarr_format: 3`, failing
  `zarr.open_group()` on everything. Every individual topic's own
  `.zgroup`/`.zattrs` (format 2) opened fine standalone, so open topic groups
  individually rather than the mission root.
- **Arrays are often padded to a fixed capacity**, for example
  `(N_scans, 25000, 3)` with a parallel `valid` count. Always slice
  `points[i, :valid[i], :]`, or you pack thousands of zero rows into the cloud.
- **Image filename to array row is positional, not by any id column.** A
  `sequence_id` field can be the original ROS stamp counter, which does not equal
  the filename index.

### 5.2 HDF5

- **`hdf5plugin` is mandatory and must be imported in every worker process** when
  arrays use Blosc2 (filter 32026) or Zstd (32015). Without it, `h5py` fails with
  `can't open directory (/usr/local/lib/plugin)`. With a process pool, the import
  has to happen inside the worker, not only in the parent.
- **Index structures beat scanning.** An event-camera stream stores a flat async
  array plus a `ms_to_idx` table mapping each millisecond to its first event.
  Using it is the difference between a slice and scanning billions of timestamps.
- **Rates vary enormously across platforms in one dataset.** Event rate varied
  more than 13x (1.0k events/ms on one platform, 13.4k on another), so any fixed
  accumulation window is empty on one and a solid smear on the other. Size the
  window per sensor to a target fill instead.
- **Sensor models can differ per platform.** One platform stored raw range images
  needing beam-intrinsic unprojection from its own embedded metadata, while
  another stored XYZ directly. Anything touching that sensor needs a
  per-platform branch.

### 5.3 PCD and point files

- `binary_compressed` PCD reads fine with `pypcd4`.
- Field lists in real files can exceed the documentation. One radar's PCD carried
  13 fields against 10 documented, with three undocumented flags. Treat unknown
  fields as opaque rather than guessing semantics.
- Organized clouds carry many `(0,0,0)` rows for non-returns. Filter by range —
  see [MCAP-TROUBLESHOOTING.md §4.2](MCAP-TROUBLESHOOTING.md#42-skip-zero-point-scans-instead-of-logging-an-empty-message).

### 5.4 CSV and text

- A free-text metadata block can precede the real header row. Skip lines until
  the expected header token appears rather than assuming line 0.
- Column semantics may not match the spec sheet. One wheel-encoder file had 2
  columns where the documented message type has 6. Flag it as unconfirmed rather
  than guessing.

### 5.5 Fitted constants, and how to avoid a wrong negative result

One dataset's only object-level data was a radar track whose scale factors are
undocumented, so they had to be fitted. The first attempt concluded the geometry
was unrecoverable. That was wrong, and how it was wrong is the lesson.

Three tests failed for reasons that had nothing to do with the radar: scoring a
detection by the image pixel it lands on conflates the unknown range scale with
the unknown mounting height and is degenerate at large ranges; regressing against
a "lead vehicle" depth kept locking onto parked cars; and one genuinely broken
field (relative velocity, `r = +0.11 / -0.08 / +0.19` across episodes) was
allowed to discredit the two good fields alongside it.

What worked was dropping to bird's-eye view and scoring against lidar points that
project onto vehicle pixels, which removes mounting height from the problem
entirely and cannot be gamed by pushing objects further away. The range scale then
showed a sharp optimum at 1/16 m per count: 67.4 % of detections within 3 m of a
vehicle, against 12.2 % at 0.05 and 19.0 % at 0.08.

The habit worth keeping: the statistics said no, and a rendered frame said yes
within seconds of looking at it. The visualization script was written only to
explain a negative result to a human, and it overturned it. **When a correlation
comes back near zero on data that ought to be structured, draw it before believing
it.** Keep the failed analyses in the repo so their failure modes stay legible —
see [MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#process-discipline).

---

## Appendix A: complete ROS 1 two-bag merge

Merges two ROS 1 bags recorded on the same rig into one MCAP episode, applying
every fix from frame/pose flattening
([MCAP-TROUBLESHOOTING.md §3](MCAP-TROUBLESHOOTING.md#3-frames-and-transforms)),
JPEG transcode
([MCAP-TROUBLESHOOTING.md §5.8](MCAP-TROUBLESHOOTING.md#58-transcoding-raw-images-and-when-not-to)),
timestamp rebasing
([MCAP-TROUBLESHOOTING.md §6.6](MCAP-TROUBLESHOOTING.md#66-rebasing-when-merging-sources)),
and §3.2–3.3 above. Adapt the prefixes, colliding frame names, and excluded
topics to your data.

```python
import heapq
from pathlib import Path

import numpy as np
from mcap.writer import Writer as McapWriter
from rosbags.rosbag1 import Reader as Reader1

# helper functions defined earlier in this guide:
#   build_typestores (3.2), resolve_msgtype (3.3), detect_frame_collision and
#   remap_frame_ids (MCAP-TROUBLESHOOTING.md#55), flatten_planar_transforms (#56),
#   repack_pointcloud2 (MCAP-TROUBLESHOOTING.md#63), detect_jpeg_topics and
#   image_to_compressed (MCAP-TROUBLESHOOTING.md#48)

A_FRAME_REMAP = {"rslidar": "a_rslidar",
                 "camera_color_optical_frame": "a_camera_color_optical_frame"}
COLLIDING_FRAMES = set(A_FRAME_REMAP)
EXCLUDE_TOPICS = set()          # topics provably derivable from retained ones (§4.4)

def register_source(reader, dst_store, writer, prefix, schema_ids, channel_ids, jpeg_topics):
    conn_to_channel = {}
    for rconn in reader.connections:
        if rconn.topic in EXCLUDE_TOPICS:
            continue
        msgtype = resolve_msgtype(rconn.msgtype)
        dst_topic = f"{prefix}{rconn.topic}"
        # channel type follows the OUTPUT representation, not the source
        if msgtype == "sensor_msgs/msg/Image" and dst_topic in jpeg_topics:
            msgtype = "sensor_msgs/msg/CompressedImage"
        if msgtype not in schema_ids:
            msgdef, _ = dst_store.generate_msgdef(msgtype, ros_version=2)
            schema_ids[msgtype] = writer.register_schema(
                name=msgtype, encoding="ros2msg", data=msgdef.encode())
        key = (dst_topic, msgtype)      # keyed by RESOLVED msgtype, see §3.3
        if key not in channel_ids:
            channel_ids[key] = writer.register_channel(
                topic=dst_topic, message_encoding="cdr", schema_id=schema_ids[msgtype])
        conn_to_channel[rconn.id] = channel_ids[key]
    return conn_to_channel

def merge(bag_a: Path, bag_b: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Reader1(bag_a) as ra, Reader1(bag_b) as rb, open(dst, "wb") as f:
        src_store, dst_store = build_typestores(ra, rb)
        b_collides = detect_frame_collision(rb, src_store, COLLIDING_FRAMES)
        jpeg_topics = (detect_jpeg_topics(ra, src_store, "/a")
                       | detect_jpeg_topics(rb, src_store, "/b"))

        writer = McapWriter(f)
        writer.start()
        schema_ids, channel_ids = {}, {}
        cm_a = register_source(ra, dst_store, writer, "/a", schema_ids, channel_ids, jpeg_topics)
        cm_b = register_source(rb, dst_store, writer, "/b", schema_ids, channel_ids, jpeg_topics)

        offset = ra.start_time - rb.start_time          # rebase
        b_remap = {n: f"b_{n}" for n in COLLIDING_FRAMES} if b_collides else {}

        def gen(reader, connmap, remap, prefix, off=0):
            for rconn, ts, data in reader.messages():
                if rconn.topic in EXCLUDE_TOPICS:
                    continue
                msgtype = resolve_msgtype(rconn.msgtype)
                msg = src_store.deserialize_ros1(data, msgtype)
                if remap:
                    msg = remap_frame_ids(msg, msgtype, remap)
                msg = flatten_planar_transforms(msg, msgtype)
                if msgtype == "sensor_msgs/msg/PointCloud2":
                    msg = repack_pointcloud2(dst_store, msg)
                if msgtype == "sensor_msgs/msg/Image" and f"{prefix}{rconn.topic}" in jpeg_topics:
                    msg = image_to_compressed(dst_store, msg)
                    msgtype = "sensor_msgs/msg/CompressedImage"
                yield ts + off, connmap[rconn.id], bytes(dst_store.serialize_cdr(msg, msgtype))

        n, first_ts, last_ts = 0, None, None
        for ts, channel_id, cdr in heapq.merge(
            gen(ra, cm_a, A_FRAME_REMAP, "/a"),
            gen(rb, cm_b, b_remap, "/b", off=offset),
            key=lambda x: x[0],
        ):
            writer.add_message(channel_id, log_time=ts, data=cdr, publish_time=ts)
            first_ts = ts if first_ts is None else min(first_ts, ts)
            last_ts = ts if last_ts is None else max(last_ts, ts)
            n += 1

        # author any static transforms neither bag records, on a topic whose path
        # segment is exactly "tf_static" (MCAP-TROUBLESHOOTING.md#52)
        # write_static_tf(writer, dst_store, schema_ids, "/a/tf_static", [...], first_ts)

        writer.finish()
    print(f"wrote {n} messages, merged duration {(last_ts - first_ts)/1e9:.2f}s -> {dst}")
```

Static transforms are authored after the message loop, using the same writer:

```python
def write_static_tf(writer, dst_store, schema_ids, topic, transforms, t_ns):
    """transforms: list of (parent, child, (x,y,z), (roll,pitch,yaw))."""
    if "tf2_msgs/msg/TFMessage" not in schema_ids:
        msgdef, _ = dst_store.generate_msgdef("tf2_msgs/msg/TFMessage", ros_version=2)
        schema_ids["tf2_msgs/msg/TFMessage"] = writer.register_schema(
            name="tf2_msgs/msg/TFMessage", encoding="ros2msg", data=msgdef.encode())
    channel_id = writer.register_channel(
        topic=topic, message_encoding="cdr", schema_id=schema_ids["tf2_msgs/msg/TFMessage"])
    data = build_static_tf_bytes(dst_store, transforms, t_ns)
    writer.add_message(channel_id, log_time=t_ns, data=data, publish_time=t_ns)

def build_static_tf_bytes(dst_store, transforms, t_ns):
    """transforms: list of (parent, child, (x,y,z), (roll,pitch,yaw)) -> CDR bytes."""
    from rosbags.typesys import Stores, get_typestore
    T = get_typestore(Stores.ROS2_FOXY).types
    sec, nsec = divmod(t_ns, 1_000_000_000)
    entries = []
    for parent, child, xyz, rpy in transforms:
        qx, qy, qz, qw = quat_from_rpy(*rpy)          # see MCAP-TROUBLESHOOTING.md#56
        entries.append(T["geometry_msgs/msg/TransformStamped"](
            header=T["std_msgs/msg/Header"](
                stamp=T["builtin_interfaces/msg/Time"](sec=int(sec), nanosec=int(nsec)),
                frame_id=parent,
            ),
            child_frame_id=child,
            transform=T["geometry_msgs/msg/Transform"](
                translation=T["geometry_msgs/msg/Vector3"](x=xyz[0], y=xyz[1], z=xyz[2]),
                rotation=T["geometry_msgs/msg/Quaternion"](x=qx, y=qy, z=qz, w=qw),
            ),
        ))
    msg = T["tf2_msgs/msg/TFMessage"](transforms=entries)
    return bytes(dst_store.serialize_cdr(msg, "tf2_msgs/msg/TFMessage"))
```

Note that a ROS `TransformStamped` always carries a `Header` with a stamp, so ROS
static transforms cannot be untimestamped the way a Foxglove `FrameTransform`
can (see [MCAP-TROUBLESHOOTING.md §3.1](MCAP-TROUBLESHOOTING.md#31-the-two-transform-stores-and-the-50-ms-rule)).
If the resulting episode reports missing transforms, that is the first thing to
test.

---

## Appendix B: complete MCAP patch tool

Adds messages to an existing MCAP without decoding or re-encoding anything else.
Use it to promote transforms, splice in a Foxglove-schema topic (see
[MCAP-TROUBLESHOOTING.md §4.1](MCAP-TROUBLESHOOTING.md#41-large-ros2-cdr-pointcloud2-can-freeze-the-app-foxglovepointcloud-does-not)),
or fix any single topic in a large file.

```python
from pathlib import Path

import yaml
from mcap.reader import make_reader
from mcap.writer import Writer

def patch_mcap(input_path: Path, output_path: Path, extra_messages,
               extra_schema=None, extra_channel=None, metadata_deltas=None):
    """
    extra_messages: list of (topic, log_time, data, publish_time). Topics must
        already exist in the source, unless extra_schema/extra_channel are given
        for a new one.
    extra_schema/extra_channel: mcap Schema/Channel records for a new topic
        (for example read out of a mini-MCAP, see MCAP-TROUBLESHOOTING.md#61).
    metadata_deltas: {topic: n_added} for the embedded rosbag2 metadata record.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_deltas = metadata_deltas or {}
    n_passthrough = 0

    with open(input_path, "rb") as fin:
        src = make_reader(fin)
        summary = src.get_summary()
        header = src.get_header()

        with open(output_path, "wb") as fout:
            writer = Writer(fout)
            writer.start(profile=header.profile, library=header.library)

            schema_id_map = {
                old_id: writer.register_schema(name=s.name, encoding=s.encoding, data=s.data)
                for old_id, s in summary.schemas.items()
            }
            channel_id_map, topic_to_new_id = {}, {}
            for old_id, c in summary.channels.items():
                new_id = writer.register_channel(
                    topic=c.topic, message_encoding=c.message_encoding,
                    schema_id=schema_id_map[c.schema_id], metadata=c.metadata or {})
                channel_id_map[old_id] = new_id
                topic_to_new_id[c.topic] = new_id

            if extra_schema is not None and extra_channel is not None:
                new_schema_id = writer.register_schema(
                    name=extra_schema.name, encoding=extra_schema.encoding,
                    data=extra_schema.data)
                topic_to_new_id[extra_channel.topic] = writer.register_channel(
                    topic=extra_channel.topic,
                    message_encoding=extra_channel.message_encoding,
                    schema_id=new_schema_id, metadata=extra_channel.metadata or {})

            # rosbag2 metadata bookkeeping (§4.2 rule 4). Only touch topics that
            # already exist there; never fabricate an entry for a spliced
            # Foxglove-schema topic (§4.2 rule 5).
            for rec in src.iter_metadata():
                if rec.name != "rosbag2" or "serialized_metadata" not in rec.metadata:
                    writer.add_metadata(name=rec.name, data=dict(rec.metadata))
                    continue
                parsed = yaml.safe_load(rec.metadata["serialized_metadata"])
                info = parsed.get("rosbag2_bagfile_information", parsed)
                topics = info.get("topics_with_message_count") or []
                added = 0
                for t in topics:
                    name = t["topic_metadata"]["name"]
                    if name in metadata_deltas:
                        t["message_count"] += metadata_deltas[name]
                        added += metadata_deltas[name]
                info["message_count"] = int(info.get("message_count", 0)) + added
                for file_info in info.get("files", []):
                    file_info["message_count"] = info["message_count"]
                writer.add_metadata(
                    name=rec.name,
                    data={"serialized_metadata": yaml.dump(parsed, default_flow_style=False,
                                                           sort_keys=False)})

            # interleave the extra messages with the byte-for-byte passthrough
            pending = sorted(extra_messages, key=lambda m: m[1])
            idx = 0

            def flush_up_to(t_ns):
                nonlocal idx
                while idx < len(pending) and pending[idx][1] <= t_ns:
                    topic, log_time, data, publish_time = pending[idx]
                    writer.add_message(channel_id=topic_to_new_id[topic], log_time=log_time,
                                       data=data, publish_time=publish_time)
                    idx += 1

            fin.seek(0)
            for _schema, channel, message in src.iter_messages():
                flush_up_to(message.log_time)
                new_id = channel_id_map.get(channel.id)
                if new_id is None:
                    continue
                writer.add_message(channel_id=new_id, log_time=message.log_time,
                                   data=message.data, publish_time=message.publish_time,
                                   sequence=message.sequence)
                n_passthrough += 1
            while idx < len(pending):
                flush_up_to(pending[idx][1])

            writer.finish()

    return {"passthrough": n_passthrough, "inserted": len(extra_messages)}
```

After patching, run `validate_mcap()`
([MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#a-written-file-is-not-a-good-file))
and confirm `message_count` equals the source count plus the number of inserted
messages.

To promote constant transforms from a dynamic topic to the static one, read the
first observed value of each rigid pair and feed those messages to the patcher:

```python
from mcap.reader import make_reader
from mcap_ros2.decoder import DecoderFactory

def find_rigid_transforms(input_path, tf_topic="/tf", base_frame="base_link"):
    """First-observed TransformStamped for every base_frame->X pair. Verify each
    is genuinely constant across the episode before using this."""
    seen = {}
    with open(input_path, "rb") as f:
        reader = make_reader(f, decoder_factories=[DecoderFactory()])
        for _schema, _channel, _msg, ros_msg in reader.iter_decoded_messages(topics=[tf_topic]):
            for tr in ros_msg.transforms:
                if tr.header.frame_id == base_frame and tr.child_frame_id not in seen:
                    seen[tr.child_frame_id] = tr
    return list(seen.values())
```
