# MCAP troubleshooting: symptoms, the viewer contract, and rendering rules

Read this when a multimodal tile isn't rendering what you expect, on files from
any path (authored, converted, or already-existing). Start with the symptom
table immediately below. If you're producing/converting MCAP files rather than
debugging one, see [MCAP-AUTHORING.md](MCAP-AUTHORING.md). For building/validating
the FiftyOne dataset itself, see [MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md).

## Contents

1. [Symptom → cause → fix triage table](#symptom--cause--fix-triage-table)
2. [The viewer contract](#2-the-viewer-contract)
3. [Frames and transforms](#3-frames-and-transforms)
4. [Point clouds](#4-point-clouds)
5. [Images, cameras, video, and calibration](#5-images-cameras-video-and-calibration)
6. [Timestamps and clock domains](#6-timestamps-and-clock-domains)

---

## Symptom → cause → fix triage table

Most of the App's rendering failures are **silent** — no error names the cause.
Check this table before assuming something is broken.

| Symptom in the App | Root cause | Fix |
|---|---|---|
| `Missing transform to <frame>`, or the 3D tile shows content "in local coordinates" | Rig extrinsics were logged with a timestamp. The viewer only treats a transform as static when it carries no timestamp; a timestamped edge is usable only within 50 ms of the playhead | Log static edges with no timestamp at all — [§3.1](#31-the-two-transform-stores-and-the-50-ms-rule) |
| Point clouds render briefly at the start, then vanish; Image tile keeps playing | Same cause as above, seen from the other side: a one-shot transform at `t0` covers only the beginning of playback | Omit the timestamp for true statics, or re-log a genuinely dynamic transform at every frame — [§3.1](#31-the-two-transform-stores-and-the-50-ms-rule) |
| `Missing transform to <root>` for every sensor, even after padding the dynamic backbone to the full episode | A chain mixing a dynamic hop (`odom→base`) with a static hop (`base→sensor`) did not resolve reliably | Precompute `T_root_sensor(t)` and log one direct dynamic hop per sensor, then remove that child from the static topic so it has one parent — [§3.3](#33-when-a-mixed-static-and-dynamic-chain-will-not-resolve) |
| Setting the 3D tile's reference frame makes everything disappear | Reference was a leaf frame. Resolution walks root to descendant, so from a leaf nothing resolves, not even its own ancestors | Set the reference selector to the tree root — [§3.4](#34-reference-frames-tree-roots-and-disconnected-components) |
| Whole App freezes when opening an episode with a big accumulated cloud | The ROS2-CDR `PointCloud2` decode path has a size-scaling problem the Foxglove-protobuf `PointCloud` path does not | Author large or accumulated clouds as `foxglove.PointCloud` — [§4.1](#41-large-ros2-cdr-pointcloud2-can-freeze-the-app-foxglovepointcloud-does-not) |
| `Failed to load: <topic>` on a point-cloud topic, only on some frames | The sensor returned 0 points on those scans. The message is spec-valid but the renderer chokes | Skip the log call for zero-point scans — [§4.2](#42-skip-zero-point-scans-instead-of-logging-an-empty-message) |
| Point cloud renders but the colours are wrong or washed out | Colour packed as float. Integer fields are normalised by their own max, but a float field is divided by 255 only when a value exceeds 2 | Pack colour as `uint8` — [§4.3](#43-colour-fields-stride-and-packing) |
| `Failed to load` on every `*/camera_info` channel | ROS 1 `CameraInfo` keeps uppercase `D/K/R/P`; ROS 2 renamed them lowercase, so the frustum code finds them undefined | Override `sensor_msgs/msg/CameraInfo` with canonical ROS 2 fielddefs in both typestores — [§5.1](#51-camerainfo-field-casing-silent-frustum-failure) |
| Point cloud renders, but cameras do not project | The image topic is not tied to its calibration | Set channel metadata `mcap.calibration_topic` — [§5.2](#52-pair-every-image-topic-with-its-calibration) |
| `Original and rectified camera models differ; choose the image geometry` | The topic name gives no geometry hint and the `K`+`D` model disagrees with `P` by more than the tolerance | Last path segment must contain `image` plus `raw` or `rect` — [§5.3](#53-topic-names-decide-the-camera-geometry) |
| `Rectified projection is available, but Auto cannot prove the image uses it: Unsupported distortion model 'kannala_brandt'` | Gap in the Auto rectified-projection detection for fisheye models. The calibration itself is valid, since frustums still render | Precompute the projection and log it as an `ImageAnnotations` overlay, which is decoded independently — [§5.6](#56-distortion-models) |
| Projection lands in the wrong place | Calibration `R` repeats a rotation the transform tree already applies | Set `R` to identity when the rectified frame is a real frame in the tree — [§5.4](#54-calibration-r-and-double-rotation) |
| Depth image displays but has no metric value | Encoding is `mono16` | Use `16uc1` (millimetres) or `32fc1` (metres) — [§5.5](#55-depth-and-other-non-rgb-image-data) |
| 16-bit depth PNG displays as solid black | A 700 mm value is about 1 % brightness as raw 16-bit grey, and passing the PNG through `CompressedImage` gets no depth-aware normalisation | Pre-colorize with a fixed range and colormap, then log 8-bit — [§5.5](#55-depth-and-other-non-rgb-image-data) |
| No video anywhere | Source is HEVC and the decoder only takes H.264 | Transcode to H.264 Annex-B, one access unit per message — [§5.7](#57-video) |
| No video, and it is already H.264 | The stream contains B-frames, which are rejected outright | Encode with `-bf 0` — [§5.7](#57-video) |
| `Timed out waiting for H.264 frame decode` | `h264_nvenc` bitstream. It passes `isConfigSupported` and then never emits a frame | Encode with `libx264` — [§5.7](#57-video) |
| Video plays only from frame 0 | SPS/PPS written once at the head | `-bsf:v dump_extra=freq=keyframe` — [§5.7](#57-video) |
| Telemetry cannot be plotted | The JSON channel has an auto-generated schema | Declare a JSON schema with typed properties — [MCAP-AUTHORING.md §2](MCAP-AUTHORING.md#2-authoring-gaps-in-foxglove-sdk) |
| `Frame transforms failed to load`, or `Record content length <absurd> is too large` | The file on disk is sparse: a hole of zeros sits between two chunks. The summary at the tail still parses, so nothing downstream notices | Gate every conversion on `validate_mcap()`, and run parallel pools under `spawn` — [MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#a-written-file-is-not-a-good-file) |
| A transform channel behaves as if it isn't static | The static store is keyed on the topic name, and a suffix breaks the match | Name it `/tf_static` or `/<prefix>/tf_static`, never with a suffix — [§3.2](#32-topic-naming-for-the-static-store) |
| Two sensors' clouds are visibly on different planes or tilted | Non-physical roll/pitch/z noise on a localization `/tf` chain | Flatten the specific `(parent, child)` pairs carrying it to yaw-only with `z=0` — [§3.6](#36-flattening-non-physical-pose-noise) |
| Pose or trajectory jumps erratically after merging two bags | Both sources wrote the same topic into one channel | Prefix or remap one source's topics before merging — [§3.5](#35-merging-bags-topic-collisions-and-frame_id-collisions-are-two-bugs) |
| Timeline spans days or weeks with slivers of data | Sources merged without timestamp rebasing | `offset = anchor.start_time - other.start_time` — [§6.6](#66-rebasing-when-merging-sources) |
| `struct.error: unpack_from requires a buffer of at least N bytes`, or a `UnicodeDecodeError` from a shifted string read | One typestore used for both ROS 1 deserialize and ROS 2 serialize. ROS 1's `Header` has an extra `uint32 seq` | Use two typestores — [MCAP-AUTHORING.md §3.2](MCAP-AUTHORING.md#32-ros-1-to-ros-2-cdr-by-hand-two-typestores-always) |
| `AttributeError: 'bytes' object has no attribute 'view'` while serializing | `rosbags`' CDR serializer expects sequence-of-primitive fields as numpy arrays | `np.frombuffer(payload, dtype=np.uint8)` first — [§5.8](#58-transcoding-raw-images-and-when-not-to) |
| One topic silently splits into two channels with the same name | A ROS 1 bag carries a legacy type name for a canonical type | Alias legacy msgtypes before keying anything on them — [MCAP-AUTHORING.md §3.3](MCAP-AUTHORING.md#33-legacy-msgtype-aliases) |
| Output MCAP is corrupt garbage, no error raised | Two processes wrote the same output path concurrently, with no locking | Treat the output path as a lock, and validate every file — [MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#process-discipline) |
| Authored file is absurdly large (for example 201 GB) | An accumulation topic's tuning constants were copy-pasted from a shorter episode | Run a dry-run size estimate per episode — [§4.6](#46-accumulated-map-topics-and-how-they-blow-up-file-size) |
| Build takes 27 minutes instead of 1 | A Zarr array stored as one chunk is re-decompressed on every `arr[i]` access inside a loop | Preload with `arr[:]` once, then index the numpy array — [MCAP-AUTHORING.md §5.1](MCAP-AUTHORING.md#51-zarr) |
| `can't open directory (/usr/local/lib/plugin)` from `h5py` | The arrays use Blosc2 or Zstd filters and `hdf5plugin` was not imported in that process | Import `hdf5plugin` in every worker process — [MCAP-AUTHORING.md §5.2](MCAP-AUTHORING.md#52-hdf5) |
| Grid preview is blank | Wrong stream selected for the preview | Use the grid's stream selector |
| Map tile empty | No `NavSatFix` or `LocationFix`, values are 0/NaN, or lat/lon are in radians | Check units before blaming the tile — [§6.5](#65-units-especially-for-gps) |
| A topic is listed but no tile will render it | No built-in decoder for that schema | Nothing to fix, it is Message tile only — [§2](#2-the-viewer-contract) |
| A tile shows nothing (or "No message at or before the playhead on this topic") right at the start of playback | That topic's first message may genuinely not start at `t=0` — real recording-startup delay is common | Scrub or play forward before concluding it's broken — [§6.7](#67-real-gaps-that-look-like-bugs-but-arent) |

If your symptom isn't here, check the silent-failure list below, or use the
bundle-reading technique to find the answer yourself and consider adding the
finding back to this table.

---

## 2. The viewer contract

The FiftyOne multimodal viewer accepts a narrower slice of what MCAP/ROS/Foxglove
schemas technically allow, and it mostly fails **silently**. A stream that
violates one of the rules on this page renders as nothing at all, usually with
no error naming the cause.

### Schema to tile reference

This table matches the official
[Supported schemas](https://docs.voxel51.com/user_guide/multimodal.html#supported-schemas)
list. Built-in decoders exist for ROS 1 and ROS 2 (CDR), Foxglove (protobuf and CDR),
and JSON-encoded versions of the same schemas. Anything else still appears in
the Message tile, which is fine. Note it and move on, don't treat it as a bug.

| Tile | ROS schemas | Foxglove schemas |
|---|---|---|
| Image | `sensor_msgs/msg/Image`, `sensor_msgs/msg/CompressedImage` | `RawImage`, `CompressedImage`, `CompressedVideo` (H.264 only, see [§5.7](#57-video)) |
| Image overlays | `vision_msgs/msg/Detection2DArray` | `ImageAnnotations` |
| 3D | `sensor_msgs/msg/PointCloud2`, `sensor_msgs/msg/LaserScan`, `nav_msgs/msg/OccupancyGrid`, `nav_msgs/msg/Odometry`, `nav_msgs/msg/Path`, `geometry_msgs/msg/PoseStamped`, `geometry_msgs/msg/PoseArray`, `geometry_msgs/msg/TransformStamped`, `tf2_msgs/msg/TFMessage`, `visualization_msgs/msg/Marker`/`MarkerArray`, `vision_msgs/msg/Detection3DArray` | `PointCloud`, `LaserScan`, `Grid`, `SceneUpdate`, `FrameTransform`/`FrameTransforms`, `PoseInFrame` |
| Camera frustum (drawn in the 3D tile, paired to an Image-tile topic) | `sensor_msgs/msg/CameraInfo` | `CameraCalibration` |
| Map | `sensor_msgs/msg/NavSatFix` | `LocationFix` |
| Logs | `rcl_interfaces/msg/Log` (ROS 2), `rosgraph_msgs/Log` (ROS 1) | `Log` |
| Plot | any numeric field path on a decodable topic | same |
| Message | any topic, decoded or not | same |

`diagnostic_msgs/msg/DiagnosticArray` is also a built-in ROS schema, decoded but
without a dedicated tile of its own.

A few schemas render in practice (confirmed by opening real recordings in the
App, including in this skill's own testing) but aren't in the official
Supported schemas list above, most likely because the Plot tile decodes *any*
numeric field on *any* decodable topic rather than requiring a per-schema
entry: `sensor_msgs/msg/Imu` plots its `linear_acceleration`/`angular_velocity`
fields this way. Treat schemas outside the official list as unconfirmed rather
than assuming they render, and re-check the live docs page if precision
matters.

Schemas confirmed to have **no** built-in decoder, which show up in the Message
tile only: `sbg_driver/msg/*` (a rich GNSS/INS vendor format), `can_msgs/msg/Frame`,
`bond/msg/Status`, `rosbag2_interfaces/*`, `lifecycle_msgs/*`, Livox's
`livox_ros_driver/msg/CustomMsg`, and raw vendor packet blobs like
`ouster_ros/msg/PacketMsg`.

Mixing ROS-schema topics and Foxglove-schema topics in a single `.mcap` is
supported and works. This matters when authoring large point clouds. See
[§4.1](#41-large-ros2-cdr-pointcloud2-can-freeze-the-app-foxglovepointcloud-does-not).

**A topic's name is not a reliable signal for what it renders as.** A topic
named `/lidar` or `/imu_packets` looks like LiDAR or IMU data, but if its actual
message schema isn't in the table above, it will never render in the 3D or
Plot tile no matter how the topic is named. It always falls back to the
Message tile. Derive capability flags (`has_pointcloud`, `has_image`, etc.) from
real schema names read out of the file, never from topic-name substrings. See
[MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#capability-flags-from-schemas-not-topic-names).

### The silent-failure list

Every one of these renders as nothing, with no error naming the cause.

| Rule | Where it's explained |
|---|---|
| Static transforms must carry no timestamp; a timestamped one expires 50 ms after the playhead passes it | [§3.1](#31-the-two-transform-stores-and-the-50-ms-rule) |
| The static store is populated from topics whose name matches `tf_static`, and holds at most 256 messages | [§3.2](#32-topic-naming-for-the-static-store) |
| A chain mixing a static hop and a dynamic hop may not resolve; precompute a direct dynamic hop instead | [§3.3](#33-when-a-mixed-static-and-dynamic-chain-will-not-resolve) |
| The 3D tile's reference frame must be the tree root, since resolution walks root to descendant | [§3.4](#34-reference-frames-tree-roots-and-disconnected-components) |
| An image topic needs `mcap.calibration_topic` channel metadata to project against its calibration | [§5.2](#52-pair-every-image-topic-with-its-calibration) |
| The topic's last path segment must contain `image` plus `raw` or `rect` when `K`+`D` and `P` disagree | [§5.3](#53-topic-names-decide-the-camera-geometry) |
| Depth needs `16uc1` (millimetres) or `32fc1` (metres); `mono16` displays but carries no metric value | [§5.5](#55-depth-and-other-non-rgb-image-data) |
| Calibration `R` must be identity when the rectified frame is itself a frame in the tree | [§5.4](#54-calibration-r-and-double-rotation) |
| Video must be H.264, no B-frames, `libx264` not `h264_nvenc`, SPS/PPS on every keyframe | [§5.7](#57-video) |
| Point cloud colour fields should be `uint8`, because float colour is ambiguous | [§4.3](#43-colour-fields-stride-and-packing) |
| A zero-point cloud message makes the topic fail to load on that frame | [§4.2](#42-skip-zero-point-scans-instead-of-logging-an-empty-message) |
| JSON channels need a declared schema to be plottable | [MCAP-AUTHORING.md §2](MCAP-AUTHORING.md#2-authoring-gaps-in-foxglove-sdk) |

### Answering viewer questions yourself

None of the above is officially documented in most places. It was recovered from
the shipped JavaScript bundle, and you can do the same when this skill goes
stale or your FiftyOne version differs:

```bash
cd "$(python -c 'import fiftyone, os; print(os.path.dirname(fiftyone.__file__))')/server/static/assets"
ls index-*.js playback-worker-*.js
```

`index-*.js` holds the scene graph, transform resolution, and camera models.
`playback-worker-*.js` holds the MCAP decode path: schemas, image encodings,
point fields. Filenames carry a content hash and change with every FiftyOne
version, so glob them. The code is minified but keeps string literals, which is
enough.

Three approaches that worked:

1. **Grep the error text you see in the UI**, with a wide context window, to find
   the function that produced it: `rg -o '.{700}Original and rectified.{500}'`.
2. **Follow the minified identifiers.** They are stable within one bundle, so
   once you have a name like `boundaryClampNs` or `addStatic`, grep it to find
   callers and defaults: `rg -o 'f4e=.{0,300}'`.
3. **Grep the schema name or encoding string you are about to emit**, to see
   whether it is handled at all: `rg -o 'case"mono16".{0,700}'`.

Two habits that repeatedly paid off:

- **Verify by rendering, not by reasoning.** Extrinsics that look right in a
  matrix are worthless as evidence. Project the lidar into the camera and check
  whether tree trunks land on tree trunks. Read colours back out of the written
  MCAP and re-project them to prove the packing and field offsets are right.
- **Check what you actually wrote, not what you meant to write.** A roughly
  20-line varint walker over a protobuf payload answers "is field 1 present?"
  without needing the schema, which is how an untimestamped-transform fix was
  once confirmed. It is the fastest way to prove a field is absent.

If the viewer reports a timeout on a video bitstream that looks conformant, the
decisive test is a standalone HTML page driving `VideoDecoder` with the same
one-chunk-in, one-frame-out logic as the viewer, fed both candidate encodings.
Reproducing a suspected platform bug outside the app is much faster than
bisecting inside it.

---

## 3. Frames and transforms

More than half of the "the viewer is broken" symptoms observed across real
imports were transform problems. §3.1 is the mechanism; everything else follows
from it.

### 3.1 The two transform stores, and the 50 ms rule

Recovered by reading the viewer bundle (see [above](#answering-viewer-questions-yourself)).
The viewer keeps two stores:

- **Static.** Populated by a bootstrap pass over topics whose name matches
  `tf_static`, holding at most **256 messages**, and keeping **only the
  transforms whose timestamp field is absent**. These are valid for all time.
- **Dynamic.** Everything else. A sample is usable only within `boundaryClampNs`
  of the playhead, which is **50 ms**.

So the natural thing to write, rig extrinsics stamped once at `t=0` on
`/tf_static`, resolves for the first 50 ms of playback and is reported missing
forever after. Omit the timestamp and it holds:

```python
import numpy as np
from scipy.spatial.transform import Rotation
from foxglove.messages import FrameTransform, Quaternion, Vector3

def transform_from_matrix(t_ns, parent, child, T):
    """FrameTransform for a 4x4 matrix. Omit t_ns to make the edge valid for all time.

    The viewer only treats a transform as static when it carries no timestamp,
    and a timestamped edge is usable only within 50 ms of the playhead.
    """
    x, y, z, w = Rotation.from_matrix(np.asarray(T[:3, :3], dtype=np.float64)).as_quat()
    stamp = {} if t_ns is None else {"timestamp": ts(t_ns)}
    return FrameTransform(
        parent_frame_id=parent,
        child_frame_id=child,
        translation=Vector3(x=float(T[0, 3]), y=float(T[1, 3]), z=float(T[2, 3])),
        rotation=Quaternion(x=float(x), y=float(y), z=float(z), w=float(w)),
        **stamp,
    )
```

The corollary: a frame relationship that genuinely changes over time must be
emitted as repeated dynamic samples, at the rate of whatever it is attached to.
In one dataset, `world` (GPS-fused) and `map` (lidar-inertial) drift 28 m and 5.6°
apart over 53 s, so they get one edge per fused pose. Chaining them with a single
static offset would look right at `t=0` and be wrong everywhere else.

When you cannot omit the timestamp, for example because you are converting a bag
whose `/tf` carries stamped transforms, the workaround is to re-log the constant
value at every frame, which keeps a sample within the clamp window at all times:

```python
for i, scan_id in enumerate(scan_ids):
    t_ns = t0_ns + i * dt_ns
    tf_ch.log(build_static_tf(calib, t_ns), log_time=t_ns)   # same values, new stamp
```

That cost a few hundred bytes per scan and fixed point clouds that had been
disappearing partway through playback. After the fix, the transform topic's
message count equals every other topic's count per episode, which is a cheap
invariant to assert.

Note that a ROS `TransformStamped` always carries a `Header` with a stamp, so ROS
static transforms cannot be untimestamped the way a Foxglove `FrameTransform`
can — if a conversion reports missing transforms, that's the first thing to
test. See [MCAP-AUTHORING.md](MCAP-AUTHORING.md#4-merging-splitting-and-patching-mcap-files)
for the full ROS 1→2 conversion path.

### 3.2 Topic naming for the static store

Both readings of the bundle agree that a topic named `/tf_static`, or
`/<prefix>/tf_static`, lands in the static store. One reading has the tokenizer
splitting on `[/.:-]+` so that a path segment must be exactly `tf_static`;
another describes it as tokenizing to `tf` plus `static`. Naming the topic
`tf_static` satisfies both.

What is verified in practice: a suffix breaks it. A topic named
`/grs/tf_static_authored` silently behaved as a dynamic channel. Multiple static
channels under different prefixes work fine, which is useful when merging
sources: `/tf_static`, `/grs/tf_static`, `/robot/tf_static`,
`/connector/tf_static` were all in use in one merged episode.

The 256-message cap means you should batch rig extrinsics into a small number of
`FrameTransforms` messages rather than one message per edge per frame.

Historical note worth keeping: a topic-naming bug and a `CameraInfo` casing bug
(see [§5.1](#51-camerainfo-field-casing-silent-frustum-failure)) once presented
as the same symptom, and fixing the first did not clear it. Fixing one cause and
seeing the symptom persist is not evidence the fix was wrong.

### 3.3 When a mixed static and dynamic chain will not resolve

One import hit a wall that §3.1 does not obviously explain. Every sensor reported
`Missing transform to odom`, including sensors exactly one static hop from `base`,
and it persisted after the dynamic `odom → base` edge was correctly padded to
cover the full episode. Flattening two static hops into one was real progress and
still not sufficient.

What worked was removing the chaining entirely. For every actively rendered
sensor, precompute the full root-to-sensor transform and log it as a single
direct dynamic hop:

```python
DIRECT_ODOM_SENSORS = {          # frame_id -> T_base_sensor (static, from calibration)
    "alphasense_right": t_base_alpharight,
    "hdr_front": t_base_hdrfront,
    "livox_lidar": t_base_livox,
}

# per sensor, at that sensor's own timestamps:
T_odom_sensor = odom_lookup(t) @ T_base_sensor
log_tf(child_frame_id=sensor_frame, t_ns=t_ns, *decompose(T_odom_sensor))

# and remove those same children from the static topic, so no frame has two parents
static_frame_transforms = [
    ft for ft in all_static if ft.child_frame_id not in DIRECT_ODOM_SENSORS
]
```

Two requirements, both sides of it:

1. Log the direct `root → sensor` hop at that sensor's own timestamps, using
   interpolation or extrapolation of the pose track. Doing it at the sensor's own
   rate also solves the coverage problem in §3.4 for free.
2. Remove the same `child_frame_id` from the static topic, or the frame ends up
   with two registered parents.

**A likely explanation, not verified.** That import logged its static transforms
*with* a timestamp, which by §3.1's rule would have kept them out of the static
store entirely and made them dynamic samples valid for 50 ms around `t=0`. That
alone would produce exactly the reported symptom. The two findings come from
different machines and possibly different FiftyOne versions, and neither was
tested against the other. If you hit this, try the untimestamped static edge
first, since it is a one-line change, and fall back to precomputed direct hops if
that does not clear it.

### 3.4 Reference frames, tree roots, and disconnected components

The 3D tile resolves relative to a reference frame, and the resolver walks root to
descendant, not descendant to root. Picking a leaf frame (say a lidar) as the
reference strands everything else, including that leaf's own ancestors. If the
scene looks empty, check the reference-frame selector before suspecting your data.

A dataset can legitimately have several disconnected coordinate roots. One had
four: leg-odometry `odom`, a SLAM `dlio_map`, a GNSS `enu_origin`, and an external
total-station frame with no parent at all. That is intentional, since the point is
comparing independent localization solutions, and there is no real calibration
linking them. The practical consequence is that only one connected component
resolves as "the scene" at a time. Don't force them into one tree.

Also make sure the backbone transform covers the whole episode, not just its own
native sample range. In one mission a camera's first frame was 0.15 s before the
first odometry sample, and other streams ran up to 17 s past the last one, so
anything under `base` had no resolvable transform at the start and end of
playback:

```python
def global_time_span(topics):
    """[first, last] across every stream, so the backbone transform can be padded
    to cover the whole episode rather than one topic's narrower span."""
    lo = hi = None
    for name in topics:
        t = timestamps_for(name)
        lo = t[0] if lo is None else min(lo, t[0])
        hi = t[-1] if hi is None else max(hi, t[-1])
    return lo, hi

# hold the first and last real pose at the global start and end
if t_lo < odom_ts[0]:
    log_tf("base", ts_ns(t_lo), pose_pos[0], pose_orien[0])
...
if t_hi > odom_ts[-1]:
    log_tf("base", ts_ns(t_hi), pose_pos[-1], pose_orien[-1])
```

The stream that starts earliest or ends latest is not the same sensor across
missions, so re-run this per episode rather than hardcoding it.

### 3.5 Merging bags: topic collisions and `frame_id` collisions are two bugs

When two bags from the same rig are merged (for example a stationary ground-truth
station plus the robot), you can hit both:

1. **Topic collision.** Both write `/camera/color/*` and `/rslidar_points`, and a
   naive merge interleaves them into one channel, producing an erratic jumping
   pose track. Fix: prefix every topic per source (`/grs`, `/robot`).
2. **`frame_id` collision.** The same two sensors also share `frame_id` strings.
   Topic prefixing does not fix this, because `frame_id` lives inside each
   message's `Header`. Left unfixed, a stationary sensor and a moving one
   silently resolve to the same tf frame.

Detect collisions by peeking one message per connection, which is enough to see
its `frame_id` values:

```python
def detect_frame_collision(reader, src_store, colliding_frames):
    for conn in reader.connections:
        for _, _, data in reader.messages(connections=[conn]):
            msgtype = resolve_msgtype(conn.msgtype)       # see MCAP-AUTHORING.md#33
            msg = src_store.deserialize_ros1(data, msgtype)
            frame_ids = set()
            if hasattr(msg, "header") and hasattr(msg.header, "frame_id"):
                frame_ids.add(msg.header.frame_id)
            elif msgtype.endswith("TFMessage"):
                for tr in msg.transforms:
                    frame_ids.add(tr.header.frame_id)
                    frame_ids.add(tr.child_frame_id)
            if frame_ids & colliding_frames:
                return True
            break        # one message per connection is enough
    return False

def remap_frame_ids(msg, msgtype, remap):
    if hasattr(msg, "header") and hasattr(msg.header, "frame_id"):
        if msg.header.frame_id in remap:
            msg.header.frame_id = remap[msg.header.frame_id]
    elif msgtype.endswith("TFMessage"):
        for tr in msg.transforms:
            if tr.header.frame_id in remap:
                tr.header.frame_id = remap[tr.header.frame_id]
            if tr.child_frame_id in remap:
                tr.child_frame_id = remap[tr.child_frame_id]
    return msg
```

Rename only the specific colliding names. Leave `base_link`, `odom`, `map`, and
`camera_link` alone, since blanket renaming breaks the real chains.

### 3.6 Flattening non-physical pose noise

Symptom: two lidars that should sit on the same floor plane render tilted or
offset relative to each other, and the offset changes whenever the pose updates.

The case that produced this fix: a wheeled ground robot's `/tf` carried
`odom→base_link` and `map→odom` with roll and pitch standard deviation of 1–6°
per scene, peaks up to ±60°, and z swinging over a meter within one episode, all
physically impossible on a flat floor. Cross-checking the same bag's `/amcl_pose`
showed exactly `roll=pitch=z=0.0` on every message, since AMCL only estimates 2D
pose. Some other 3D pose-fusion node was writing the noisy values, and that noise
sat on the only path from the robot's sensors up to the `map` frame.

Flatten only the pairs that carry the noise, keeping x, y, and yaw:

```python
import math

PLANAR_TF_PAIRS = {("odom", "base_link"), ("map", "odom")}

def quat_from_rpy(roll, pitch, yaw):
    cr, sr = math.cos(roll / 2), math.sin(roll / 2)
    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
    return (sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
            cr * cp * cy + sr * sp * sy)       # x, y, z, w

def _yaw_from_quat(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))

def flatten_planar_transforms(msg, msgtype, pairs=PLANAR_TF_PAIRS):
    """Force listed (parent, child) transforms to pure 2D: keep x/y and yaw,
    zero z, discard roll/pitch. No-op for every other message type or pair."""
    if not msgtype.endswith("TFMessage"):
        return msg
    for tr in msg.transforms:
        if (tr.header.frame_id, tr.child_frame_id) not in pairs:
            continue
        qx, qy, qz, qw = quat_from_rpy(0.0, 0.0, _yaw_from_quat(tr.transform.rotation))
        tr.transform.rotation.x, tr.transform.rotation.y = qx, qy
        tr.transform.rotation.z, tr.transform.rotation.w = qz, qw
        tr.transform.translation.z = 0.0
    return msg
```

Before applying this, verify the transforms you are not touching are real:
constant static mounts and genuine wheel-joint rotation should be left alone.

### 3.7 Frames that cannot be connected, and conventions that bite

Recognize and document these, don't patch them:

- No `CameraInfo` or `CameraCalibration` anywhere means no camera frustum.
- No recorded extrinsics means per-sensor point clouds cannot be registered
  against each other, except any the robot's own stack pre-fused.
- A `header.frame_id` that appears in no transform anywhere (one camera's
  `..._optical` frame was absent from both `/tf` and `/tf_static` in the entire
  source) cannot be bridged without inventing a calibration.

Conventions that cost real time:

| Trap | What was wrong | Correct handling |
|---|---|---|
| A devkit applies `world_point = Rz(yaw) @ (p + offset)` | A TF parent→child is `R @ p + t`, so `t = R @ offset`, not `offset` | Expand the devkit's own expression algebraically before turning it into a transform |
| Paper and launch file specify a 15° downward lidar tilt | The raw cloud's floor was already flat in its own frame, and re-applying 15° sloped it by about 2 m across the room | Went with the sensor data and flagged the discrepancy rather than silently overriding it |
| A devkit's transform helper names its variables backwards, setting `child = attrs["base_frame_id"]` | Verified `base_frame_id` is always the physical parent, since the tree root never appears as a child | Trust the plain keys, not the helper's variable names, and re-derive the composition yourself |
| A devkit's box-heading helper reads `center3D` where it means `rotation3D` | Genuine devkit bug | Read `rotation3D.z` directly |
| Devkit comments say sequence A uses calibration `param_a` | Its shipped files actually matched `param_b`, and two sequences differed by several degrees of boresight | Parse calibration fresh from each sequence's own shipped files |
| Raw quaternion arrays | Stored as `[x, y, z, w]`, not `[w, x, y, z]`. Verified by checking that the devkit feeds them straight into `scipy.Rotation.from_quat()` with no reordering | Check the devkit's own usage before assuming an order |
| A payload mounted 180° flipped about X relative to the robot base | A genuine calibrated fact, not a bug: the quaternion is exactly `w≈0, x≈-1` | Sanity-check by transforming a real scan and confirming points land below the base, not above |
| Camera orientation columns are Omega/Phi/Kappa | Photogrammetric convention `M = Rz(κ)·Ry(φ)·Rx(ω)` maps ground (ENU) to camera, so `world_from_camera = M.T` | Confirm by checking `M.T`'s local-X column against real heading |
| Optical-frame convention | ROS camera drivers use a fixed `rpy = (-90°, 0, -90°)` from `camera_link` to `*_optical_frame`. Universal, not robot-specific | Author it when the bag omits it |
| Calibration files giving `roll/pitch/yaw` | ROS `tf2::Quaternion::setRPY` is intrinsic ZYX | Use the matching conversion below |

```python
import numpy as np
from foxglove.messages import Quaternion

def rpy_to_quat(roll, pitch, yaw):
    """Intrinsic ZYX (yaw-pitch-roll), matching ROS tf2 Quaternion::setRPY."""
    cr, sr = np.cos(roll / 2.0), np.sin(roll / 2.0)
    cp, sp = np.cos(pitch / 2.0), np.sin(pitch / 2.0)
    cy, sy = np.cos(yaw / 2.0), np.sin(yaw / 2.0)
    return Quaternion(
        w=float(cr * cp * cy + sr * sp * sy),
        x=float(sr * cp * cy - cr * sp * sy),
        y=float(cr * sp * cy + sr * cp * sy),
        z=float(cr * cp * sy - sr * sp * cy),
    )
```

XML calibration files often declare a default namespace, which makes every tag
namespace-qualified and breaks `ElementTree.find()` with plain tag names:

```python
import xml.etree.ElementTree as ET

def parse_xml_strip_ns(path):
    tree = ET.parse(path)
    for el in tree.getroot().iter():
        if "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return tree.getroot()
```

**Verify calibration numerically, never against the paper alone.** Papers and
devkits have been wrong or self-contradictory across multiple real imports.
Cheap checks that caught real bugs: lidar z-spread before/after a boresight (31 m
to 12.7 m, confirming gravity-alignment of a tilted scanner); a rotation
matrix's local-X column against heading from consecutive position deltas
(agreeing to about 1°); a derived IMU position holding a constant lever arm from
the camera across a whole sequence; a z-histogram of a real scan clustering
below the robot, not above; projecting the lidar into the camera and checking
points land on real scene geometry.

---

## 4. Point clouds

### 4.1 Large ROS2-CDR `PointCloud2` can freeze the App; `foxglove.PointCloud` does not

Isolated over four rounds of otherwise-correct byte-level fixes, with
side-by-side testing on the same episode. The episode loaded fine without the
topic, and a different dataset ships `foxglove.PointCloud` messages up to 30.6 MB
with no issue, 4x larger than the ROS2-CDR `PointCloud2` attempt that froze the
App every time. So this is not about message size. The ROS2-CDR `PointCloud2`
decode path has a scaling problem the Foxglove-protobuf `PointCloud` path does
not.

Rule: author any large or accumulated cloud as `foxglove.PointCloud`. Ordinary
per-scan ROS `PointCloud2` topics work fine at their own much smaller per-message
size, so leave those alone.

To add a Foxglove-schema topic to an existing ROS 2 MCAP, note that
`foxglove-sdk`'s writer is a compiled extension with no "serialize this message
to bytes" API. Author into a throwaway mini-MCAP, then splice the bytes:

```python
import tempfile
from pathlib import Path

import numpy as np
import foxglove
from foxglove.channels import PointCloudChannel
from foxglove.messages import (
    PackedElementField, PackedElementFieldNumericType, PointCloud, Timestamp,
)
from mcap.reader import make_reader

def author_mini_mcap(topic, frame_id, snapshots):
    """snapshots: list of (t_ns, xyz float32 array). Returns a temp .mcap path."""
    f32 = PackedElementFieldNumericType.Float32
    fields = [PackedElementField(name=n, offset=4 * i, type=f32)
              for i, n in enumerate(("x", "y", "z"))]
    tmp_path = Path(tempfile.mkstemp(suffix=".mcap")[1])
    tmp_path.unlink()                    # open_mcap requires the path not to exist
    ch = PointCloudChannel(topic=topic)
    with foxglove.open_mcap(str(tmp_path)):
        for t_ns, xyz in snapshots:
            sec, nsec = divmod(t_ns, 1_000_000_000)
            ch.log(
                PointCloud(
                    timestamp=Timestamp(sec=int(sec), nsec=int(nsec)),
                    frame_id=frame_id, point_stride=12, fields=fields,
                    data=np.ascontiguousarray(xyz, dtype=np.float32).tobytes(),
                ),
                log_time=t_ns,
            )
    return tmp_path

def read_spliceable(mini_path, topic):
    """Returns (schema, channel, [(log_time, data, publish_time), ...])."""
    with open(mini_path, "rb") as f:
        reader = make_reader(f)
        summary = reader.get_summary()
        schema = next(s for s in summary.schemas.values() if s.name == "foxglove.PointCloud")
        channel = next(c for c in summary.channels.values() if c.topic == topic)
        f.seek(0)
        msgs = [(m.log_time, m.data, m.publish_time)
                for _s, c, m in reader.iter_messages() if c.id == channel.id]
    return schema, channel, msgs
```

Then register that schema and channel on the output writer and interleave the
messages by `log_time` using the patch tool in
[MCAP-AUTHORING.md](MCAP-AUTHORING.md#appendix-b-complete-mcap-patch-tool).

### 4.2 Skip zero-point scans instead of logging an empty message

A 0-point cloud is spec-valid (correct `point_stride`, `fields`, `frame_id`,
0-byte `data`) and decodes fine at the MCAP layer, but the 3D tile shows
`Failed to load: <topic>` on those frames. Some sensors are silent a lot: one
dataset's rear low-resolution lidar returned 0 points on 74 of 79 scans in one
scene, and up to about 95 % in others, while the front unit was never empty.

```python
if pts.shape[0] == 0:
    continue          # sensor silence stays silence: no message, no fake points
```

After the fix, zero-length messages on that topic went from 74 to 0, with the 5
real non-empty scans preserved.

A related but different case: a lidar that emits zero-return placeholder points
at the origin. Those are real messages with junk points, so filter by range
rather than dropping the message:

```python
mask = np.linalg.norm(pts[:, :3], axis=1) > 0.5     # metres
pts = pts[mask]
```

### 4.3 Colour fields, stride, and packing

**Colour fields** are `r`/`red`, `g`/`green`, `b`/`blue`, `a`/`alpha`, or a packed
`color`/`rgb`/`rgba`. Integer types are normalised by their own maximum, so
`uint8` 0–255 is right. A float field is divided by 255 only when a value exceeds
2, which makes float colour ambiguous. Use `uint8`.

**Mixed numeric types in one cloud work**, and a numpy structured dtype is the
reliable way to build the buffer. Getting `point_stride` wrong silently
misaligns every field:

```python
F32 = PackedElementFieldNumericType.Float32
U8 = PackedElementFieldNumericType.Uint8

POINT_STRIDE = 20                     # x,y,z,intensity float32 then r,g,b,a uint8
POINT_FIELDS = [
    PackedElementField(name=n, offset=o, type=F32)
    for n, o in (("x", 0), ("y", 4), ("z", 8), ("intensity", 12))
] + [
    PackedElementField(name=n, offset=o, type=U8)
    for n, o in (("red", 16), ("green", 17), ("blue", 18), ("alpha", 19))
]

def pack_points(pts, colors):
    """(N,4) float32 xyz+intensity and (N,4) uint8 rgba -> 20-byte records."""
    buf = np.empty((len(pts), POINT_STRIDE), dtype=np.uint8)
    buf[:, :16] = np.ascontiguousarray(pts).view(np.uint8).reshape(len(pts), 16)
    buf[:, 16:] = colors
    return buf.tobytes()
```

**Watch alignment when mixing widths.** A layout of `x,y,z` (float32) plus
`r,g,b` (uint8 at offsets 12, 13, 14) plus four float32 fields starting at offset
16, stride 32, leaves a deliberate one-byte gap at offset 15 so the float32 block
stays 4-byte aligned.

**Undeclared padding is common in source data.** One dataset's lidar declared
`point_step = 32` while its own `PointField` list (x, y, z, intensity at 4 bytes
each) spanned only 16, wasting 16 bytes per point. Repacking to a tight stride is
a no-op on already-tight messages, so it can run unconditionally:

```python
# sensor_msgs/msg/PointField.datatype -> byte width (stable ROS constants)
POINTFIELD_SIZES = {1: 1, 2: 1, 3: 2, 4: 2, 5: 4, 6: 4, 7: 4, 8: 8}

def repack_pointcloud2(dst_store, msg):
    """Rebuild a PointCloud2 using only its own declared fields, tightly packed."""
    n_pts = msg.width * msg.height
    old_step = msg.point_step
    raw = np.frombuffer(bytes(msg.data), dtype=np.uint8).reshape(n_pts, old_step)

    chunks, new_fields, offset = [], [], 0
    for fld in msg.fields:
        size = POINTFIELD_SIZES[fld.datatype] * max(fld.count, 1)
        chunks.append(raw[:, fld.offset:fld.offset + size])
        new_fields.append(fld.__class__(name=fld.name, offset=offset,
                                        datatype=fld.datatype, count=fld.count))
        offset += size
    if offset == old_step:
        return msg                                   # already tight

    PointCloud2 = dst_store.types["sensor_msgs/msg/PointCloud2"]
    return PointCloud2(
        header=msg.header, height=msg.height, width=msg.width, fields=new_fields,
        is_bigendian=msg.is_bigendian, point_step=offset,
        row_step=offset * msg.width,
        data=np.ascontiguousarray(np.concatenate(chunks, axis=1)).reshape(-1),
        is_dense=msg.is_dense,
    )
```

Honest accounting of that win: uncompressed bytes halved, but measured on-disk
saving across 7 episodes was only 5.2 % (31.5 GB down to 29.8 GB), because 12 of
the 16 wasted bytes were near-always zero and already squashed by MCAP's chunk
compression. The defensible win is roughly 50 % less per-message CPU decode cost
on the largest channel. Don't oversell padding fixes as file-size fixes.

**Downcast only when provably lossless.** One dataset packs intensity as `uint8`
(19 down to 16 byte stride) after verifying intensity is always an exact integer
in `[0, 255]` on real scans, and asserts it per scan so a future sequence raises
loudly instead of silently clipping:

```python
raw_intensity = xyzi[:, 3]
if n and (np.any(raw_intensity != np.round(raw_intensity))
          or raw_intensity.min() < 0 or raw_intensity.max() > 255):
    raise ValueError(f"{path}: intensity not representable as uint8 losslessly")
```

**PCL "packed float rgb"** must be unpacked into separate `uint8` fields:

```python
packed = pc.numpy(("rgb",)).ravel().astype(np.float32).view(np.uint32)
red   = (packed >> 16) & 0xFF
green = (packed >> 8) & 0xFF
blue  = packed & 0xFF
```

Point clouds need at least two of `x`/`y`/`z`.

### 4.4 Coloring point clouds with real color

Project each point into the nearest-in-time image through the calibrated
lidar-to-camera transform and sample the image. Rules that kept it honest:

- sample from the full-resolution source image even when the embedded image topic
  is downsampled for display (see [§5.8](#58-transcoding-raw-images-and-when-not-to));
- points with no valid projection fall back to greyscale-from-intensity, never a
  fabricated color;
- validate before running at scale. Render one scan's projected points colored by
  depth, overlaid on the image, and check that they land on real geometry.

```python
# rgb starts as greyscale-from-intensity, then valid projections overwrite it
intensity_norm = np.clip(raw_intensity / max(float(raw_intensity.max()), 1.0), 0, 1)
grey = (intensity_norm * 200 + 40).astype(np.uint8)      # avoid pure black
rgb = np.stack([grey, grey, grey], axis=1)
rgb[valid] = image_array[row_i[valid], col_i[valid]]
```

For a multi-camera rig, let the first camera that sees a point win, and leave
uncovered points grey:

```python
colored = np.zeros(len(points), dtype=bool)
for cam in cameras:
    u, v, orig_idx = project(points, cam)
    new = ~colored[orig_idx]
    rgb[orig_idx[new]] = cam.image[v[new], u[new]]
    colored[orig_idx[new]] = True
```

Read the colours back out of the written MCAP and re-project them to prove the
packing and field offsets are right. A byte-for-byte comparison of decoded x/y/z
against the raw source, before and after adding RGB fields, is what proved
colorization never touched a coordinate.

### 4.5 Semantic and label coloring

Share one `class → color` map across every tile (radar points, camera 2D boxes,
lidar 3D boxes) so a class reads identically everywhere.

A real bug lived here for a while: box geometry was correct 1:1 against the
source JSON, verified by counting boxes per scan, but the class-name field was
never read, so every box rendered identical plain green. Geometry being right is
not evidence the labels are right, so check both.

### 4.6 Accumulated "map" topics, and how they blow up file size

They exist because a single-scan topic flickers hard: each message fully replaces
the last, points-per-scan can swing 5x scan to scan, and pose often updates slower
than the lidar. An accumulated topic shows everything seen up to the current
playback time.

Voxel-hash all points, take each voxel's first chronological occurrence, and sort
by index. Then `map_points[:k]` is exactly "the map as of the k-th new voxel", and
producing the message at any time is a binary search rather than a rebuild:

```python
voxel_idx = np.floor(all_xyz / voxel_size).astype(np.int64)
keys = voxel_idx[:,0]*73856093 ^ voxel_idx[:,1]*19349663 ^ voxel_idx[:,2]*83492791
_, first_idx = np.unique(keys, return_index=True)
first_idx = np.sort(first_idx)            # k-th NEW voxel, in order of appearance
map_points, map_time = all_xyz[first_idx], all_time[first_idx]

for t_ns in output_times:
    count = int(np.searchsorted(map_time, t_ns, side="right"))   # O(log n)
    if count == 0:
        continue
    map_ch.log(PointCloud(..., data=map_points[:count].tobytes()), log_time=t_ns)
```

Output size scales as `n_messages × final_voxel_count`, and both factors scale
with route length and duration rather than point count. One sequence's tuned
`(0.2 m, 2 Hz)` settings, reused unchanged on an 11x-longer sequence, produced a
201 GB file before anyone checked: 13x bigger final map times 6.7x more messages
is roughly 87x. The longer sequence ended up at `(0.75 m, 0.5 Hz)`.

Run this dry-run estimate before committing to settings for any new episode:

```python
BYTES_PER_POINT = 16          # your point stride

for voxel in (0.2, 0.5, 0.75, 1.0):
    idx = np.floor(all_xyz / voxel).astype(np.int64)
    keys = idx[:,0]*73856093 ^ idx[:,1]*19349663 ^ idx[:,2]*83492791
    n_vox = len(np.unique(keys))
    for hz in (0.5, 1.0, 2.0):
        n_msgs = int(duration_s * hz)
        print(voxel, hz, f"{n_vox * n_msgs * BYTES_PER_POINT / 1e9:.1f} GB (upper bound)")
```

It is an upper bound, since early messages carry fewer voxels, but it is the
number that would have caught the 201 GB file.

Policy that came out of it: voxel size and update rate are a required per-episode
pair, never a shared constant, and bias toward larger voxels and lower rate. The
topic carries zero unique information, since the raw per-scan topic already has
every point, and it was about 55 % of one episode's total file size. See
[MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#size-buffering-speed-and-cost)
for how this ranks against other size drivers.

---

## 5. Images, cameras, video, and calibration

### 5.1 `CameraInfo` field casing (silent frustum failure)

ROS 1's `CameraInfo` message definition uses uppercase `D/K/R/P`; ROS 2 renamed
them to lowercase. It is a pure rename, with identical types, order, and count.
Carried through verbatim from a ROS 1 bag into a schema declared
`sensor_msgs/msg/CameraInfo`, the frustum code finds the canonical lowercase
fields undefined and marks the channel `Failed to load`.

```python
from rosbags.typesys import Stores, get_typestore

foxy = get_typestore(Stores.ROS2_FOXY)
camerainfo_def = {"sensor_msgs/msg/CameraInfo": foxy.FIELDDEFS["sensor_msgs/msg/CameraInfo"]}
src_store.register(dict(camerainfo_def))
dst_store.register(dict(camerainfo_def))
```

When registering the bag's own types, drop `CameraInfo` first so the bag's
uppercase definition cannot overwrite the canonical one:

```python
from rosbags.convert.converter import get_types_from_msg

typs = get_types_from_msg(conn.msgdef, conn.msgtype)
typs.pop("sensor_msgs/msg/CameraInfo", None)
src_store.register(dict(typs))
```

`CameraInfo` was the only type across four scene bags whose casing differed from
ROS 2 in one import, so a general case-folding pass is not warranted by default —
but do check for it. See [MCAP-AUTHORING.md §3.2](MCAP-AUTHORING.md#32-ros-1-to-ros-2-cdr-by-hand-two-typestores-always)
for how this fits into a full bag conversion.

### 5.2 Pair every image topic with its calibration

An image stream and a `CameraCalibration` topic are not associated by name. Set
the channel metadata explicitly, or the Image tile has nothing to project
against and the 3D tile cannot draw the frustum:

```python
channel = CompressedImageChannel(
    topic="/camera/left/image_raw",
    metadata={"mcap.calibration_topic": "/camera/left/calibration"},
)
```

The same key works for `RawImageChannel` and `CompressedVideoChannel`. Publish
the calibration once per episode for a static rig:

```python
from foxglove.channels import CameraCalibrationChannel
from foxglove.messages import CameraCalibration

calib_ch = CameraCalibrationChannel(topic="/camera/left/calibration")
calib_ch.log(
    CameraCalibration(
        timestamp=ts(t0_ns), frame_id="camera_left", width=1920, height=1456,
        distortion_model="plumb_bob",       # see §5.6 for fisheye
        D=[k1, k2, p1, p2, 0.0],
        K=K.flatten().tolist(),             # 3x3 row-major
        R=np.eye(3).flatten().tolist(),     # identity, see §5.4
        P=P[:3, :4].flatten().tolist(),     # 3x4 row-major
    ),
    log_time=t0_ns,
)
```

### 5.3 Topic names decide the camera geometry

With geometry on Auto, the viewer builds two models from one `CameraCalibration`,
`K`+`D` (original, distorted) and `P` (rectified), and picks silently only when
the two agree to within `min(1, max(0.5, diagonal × 1e-4))` px, which is 0.5 px at
1920×1456. Cameras with `k1 = -0.14` put the models 91 px apart, so Auto refuses
and nothing projects, with the message `Original and rectified camera models
differ; choose the image geometry`.

The tiebreaker is the topic's **last path segment**, scanned backwards while
skipping segments beginning with `compressed`. It must contain the token `image`,
plus `raw` for the original or `rect`/`rectified` for the rectified image. So
`/camera/left/image_raw`, not `/camera/left`.

A calibration with `D` all zeros and `P` built from `K` needs no hint, because
the two models coincide and Auto resolves it.

### 5.4 Calibration `R` and double rotation

If the rectified frame is itself a real frame in the transform tree, set the
calibration's `R` to identity. Otherwise `R` repeats a rotation the tree already
applies and the projection lands in the wrong place.

Rectification is a pure rotation plus a new pinhole `K_rect`, so rectified
products (depth, semantic, flow) belong in their own frame rather than stacked on
the raw camera's frame. See [§3](#3-frames-and-transforms) for the transform tree
itself.

### 5.5 Depth and other non-RGB image data

- **Depth encoding matters.** `mono16` displays but carries no metric value. Use
  `16uc1` for millimetres or `32fc1` for metres. `16uc1` saturates at 65.5 m, so
  ground truth reaching 102 m has to go out as `32fc1`.
- **A raw 16-bit depth PNG through `CompressedImage` displays as solid black.** A
  700 mm value is about 1 % brightness as linear 16-bit grey, and no depth-aware
  normalisation is applied. Pre-colorize with a fixed range and colormap:

  ```python
  import io
  import matplotlib
  import numpy as np
  from PIL import Image

  VIRIDIS = (matplotlib.colormaps["viridis"](np.linspace(0, 1, 256))[:, :3] * 255).astype(np.uint8)

  def colorize_depth_png(path, vmax_m=6.0):
      depth_mm = np.array(Image.open(path), dtype=np.uint16)
      valid = depth_mm > 0
      idx = np.clip((depth_mm.astype(np.float32) / 1000.0) / vmax_m, 0.0, 1.0)
      rgb = VIRIDIS[(idx * 255).astype(np.uint8)]
      rgb[~valid] = 0                       # invalid/zero return -> black
      buf = io.BytesIO()
      Image.fromarray(rgb, mode="RGB").save(buf, format="PNG")
      return buf.getvalue()
  ```

- **Radar and sonar:** render polar to cartesian and log as `mono8` `RawImage`
  with `step = width`. For sonar, run `np.nan_to_num` first. Logging both the
  polar and the cartesian BEV image is useful, since the polar image is the raw
  measurement.
- **Doppler correction can be era-dependent.** One dataset applies radar Doppler
  and offset correction only to post-upgrade recordings, because in pre-upgrade
  files the corresponding column is a validity mask and applying the correction
  corrupts the image. Gate on the frame timestamp.
- **Segmentation:** map class indices through a palette to an RGB PNG, with
  anything unlabelled going to black.
- **Audio:** `RawAudio` with `format="pcm-s16"` read straight from WAV worked in hands-on testing,
  though `foxglove.RawAudio` isn't in the official supported-schemas list, so verify playback in
  the App before relying on it.

### 5.6 Distortion models

Source `camera_info.distortion_model` values are ROS-style. Foxglove's
`CameraCalibration.distortion_model` does not recognize `equidistant`, so map it
to `kannala_brandt`, the general fisheye model that `equidistant` is a special
case of, with the same 4-parameter `D`. `plumb_bob` passes through unchanged.

```python
DISTORTION_MODEL_MAP = {"equidistant": "kannala_brandt", "plumb_bob": "plumb_bob"}
```

On the OpenCV side, projecting points for a `equidistant`/`kannala_brandt` camera
means `cv2.fisheye.projectPoints`, not `cv2.projectPoints`.

Open issue worth knowing: the 3D tile's Auto rectified-projection detection
rejects `kannala_brandt` with `Rectified projection is available, but Auto cannot
prove the image uses it: Unsupported distortion model 'kannala_brandt'`. The
calibration itself is valid, since frustums render. The workaround is to
precompute the lidar-to-image projection and log it as an `ImageAnnotations`
overlay, which is decoded independently of the calibration-driven live
projection:

- one overlay topic per camera, for example `/cam/hdr_front/lidar_overlay`;
- select it as the image's annotation source in the Image tile's settings, since
  it is not auto-paired by name;
- cap the points per (scan, camera) pair, for example 600 via a seeded random
  subsample. Logging thousands of individual `Point2` and `Color` objects
  balloons both build time and file size for no visible benefit at typical zoom;
- color by depth with a fixed `vmax`, and verify by compositing the decoded
  overlay onto the decoded RGB frame in Python rather than trusting message
  counts.

### 5.7 Video

The viewer decodes `CompressedVideo` through WebCodecs, and the constraints come
from that decode path rather than from quality goals. All four were found the
hard way, each presenting as no video at all:

| Constraint | Why |
|---|---|
| H.264 only | HEVC is not accepted |
| `-bf 0` | Streams containing B-frames are rejected outright |
| `libx264`, not `h264_nvenc` | NVENC output passes `VideoDecoder.isConfigSupported` and then never emits a frame. Verified against Chromium 144, where an NVENC stream decoded 0 of 30 frames while a libx264 stream at identical profile and level decoded 30 of 30 |
| `-bsf:v dump_extra=freq=keyframe` | Repeats SPS/PPS on every keyframe, so playback can start from any seek point rather than only frame 0 |

```python
def transcode_h264(mp4_path, out_path, stride, gop):
    """Transcode every stride-th frame of a source video to an Annex-B H.264 stream."""
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", mp4_path,
        "-vf", f"select=not(mod(n\\,{stride}))", "-vsync", "0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-g", str(gop),
        "-bf", "0", "-pix_fmt", "yuv420p",
        "-bsf:v", "dump_extra=freq=keyframe", "-f", "h264", out_path,
    ]
    subprocess.run(cmd, check=True)
    return out_path

def annexb_packets(path):
    """One access unit per message is what the viewer expects."""
    import av
    with av.open(path) as container:
        stream = container.streams.video[0]
        return [bytes(p) for p in container.demux(stream) if p.size]

channel = CompressedVideoChannel(
    topic="/camera/left/image_raw",
    metadata={"mcap.calibration_topic": "/camera/left/calibration"},
)
for i, packet in enumerate(packets):
    t_ns = epoch_ns + int(times[i] * 1e9)
    channel.log(
        CompressedVideo(timestamp=ts(t_ns), frame_id="camera_left",
                        format="h264", data=packet),
        log_time=t_ns,
    )
```

The same three encoder rules apply when generating frames yourself, feeding raw
BGR on ffmpeg's stdin with `-f rawvideo -pix_fmt bgr24 -s WxH`.

If a video stream is paired with a calibration topic, do not downscale it. The
calibration would then describe an image size that no longer exists.

Two lessons from encoding a sparse derived stream (optical flow rendered as a
colour wheel over mostly-black frames):

| Question | Answer |
|---|---|
| How to make a sparse field compress | Dilating the field is worth far more than lowering quality. At 1920×1456, a 5 px kernel at CRF 22 gave 411 KB/frame and a 9 px kernel at CRF 26 gave 107 KB, while raising CRF alone only reached 260 KB. Isolated lit pixels on black are the worst case for an inter-frame codec, and the denser render also reads better |
| Where to set the brightness normaliser | Fixed per episode, at the 75th percentile of magnitude. Per-frame normalising stretches a stationary stretch back up to full scale and makes standing still look like motion |

### 5.8 Transcoding raw images, and when not to

Raw `rgb8`/`bgr8` `Image` topics were about 76 % of one scene's uncompressed
bytes with no codec at all, and were the main reason client-side buffering of an
episode was slow. Transcoding them to JPEG-backed
`sensor_msgs/msg/CompressedImage` at quality 90 cut that roughly 10x with no
viewer changes needed.

Detect eligibility by encoding rather than topic name, so it generalizes across
scenes and platforms:

```python
JPEG_ENCODINGS = {"rgb8", "bgr8"}

def detect_jpeg_topics(reader, src_store, prefix):
    """dst_topic set for Image connections carrying a JPEG-eligible encoding."""
    jpeg_topics = set()
    for conn in reader.connections:
        if resolve_msgtype(conn.msgtype) != "sensor_msgs/msg/Image":
            continue
        dst_topic = f"{prefix}{conn.topic}"
        if dst_topic in jpeg_topics:
            continue
        for _, _, data in reader.messages(connections=[conn]):
            msg = src_store.deserialize_ros1(data, "sensor_msgs/msg/Image")
            if msg.encoding in JPEG_ENCODINGS:
                jpeg_topics.add(dst_topic)
            break
    return jpeg_topics

def image_to_compressed(dst_store, msg, quality=90):
    import io
    from PIL import Image as PILImage
    row_bytes = msg.width * 3
    frame = np.frombuffer(bytes(msg.data), dtype=np.uint8).reshape(msg.height, msg.step)
    frame = frame[:, :row_bytes].reshape(msg.height, msg.width, 3)
    if msg.encoding == "bgr8":
        frame = frame[:, :, ::-1]
    buf = io.BytesIO()
    PILImage.fromarray(frame, mode="RGB").save(buf, format="JPEG", quality=quality)
    CompressedImage = dst_store.types["sensor_msgs/msg/CompressedImage"]
    # rosbags' CDR serializer calls .view() on sequence-of-primitive fields, so
    # they must be numpy arrays, not bytes.
    jpeg_bytes = np.frombuffer(buf.getvalue(), dtype=np.uint8)
    return CompressedImage(header=msg.header, format="jpeg", data=jpeg_bytes)
```

Remaining rules:

- **Never JPEG depth.** `16UC1`, `32FC1`, and anything that isn't 8-bit
  3-channel stays raw, because JPEG is 8-bit and lossy.
- **Register the channel with the output type.** If you transcode `Image` to
  `CompressedImage`, the channel's schema must be `CompressedImage`.
- **Downsample for display where the full-resolution copy isn't needed for
  math.** Embedding 8000×4000 panoramas at 0.5 scale and JPEG quality 85 took one
  frame from 4.96 MB to 0.97 MB, and a 4500-frame sequence from about 22 GB to
  about 4.4 GB, while colorization still sampled the full-resolution file on disk.
  Do not do this when the topic is paired with a calibration (§5.7).
- **`CompressedImage.format` is not always a plain codec name.** One dataset's
  topic carries `format = "rgb8; jpeg compressed bgr8"`, where the true source
  colorspace is the last token. Custom extraction code that assumes `"jpeg"` will
  invert colors.
- **Strip alpha before re-encoding** if the source PNGs are RGBA.

### 5.9 Overlays and annotations

```python
from foxglove.channels import ImageAnnotationsChannel, SceneUpdateChannel
from foxglove.messages import (
    Color, CubePrimitive, ImageAnnotations, KeyValuePair, Point2,
    PointsAnnotation, PointsAnnotationType, SceneEntity, SceneUpdate,
    TextAnnotation, TextPrimitive,
)

# 2D box on the image tile: LineLoop for a rectangle, LineList for a projected
# 3D wireframe (pairs of endpoints), plus a text label.
ann_ch.log(
    ImageAnnotations(
        points=[PointsAnnotation(
            timestamp=ts(t_ns), type=PointsAnnotationType.LineLoop,
            points=[Point2(x=p["x"], y=p["y"]) for p in corners],
            outline_color=color, thickness=3.0,
            metadata=[KeyValuePair(key="label", value=class_name)],
        )],
        texts=[TextAnnotation(
            timestamp=ts(t_ns), position=Point2(x=x0, y=y0 - 14), text=class_name,
            font_size=12.0, text_color=Color(r=1, g=1, b=1, a=1), background_color=color,
        )],
    ),
    log_time=t_ns,
)

# 3D cuboid, with the entity id carrying a persistent track identity
box_ch.log(
    SceneUpdate(entities=[SceneEntity(
        timestamp=ts(t_ns), frame_id="lidar", id=track_uuid,
        metadata=[KeyValuePair(key="label", value=class_name)],
        cubes=[CubePrimitive(pose=pose, size=Vector3(x=l, y=w, z=h),
                             color=class_color(class_name, alpha=0.35))],
        texts=[TextPrimitive(pose=label_pose, billboard=True, scale_invariant=True,
                             font_size=14.0, text=class_name, color=color)],
    )]),
    log_time=t_ns,
)
```

Details that matter:

- **Entity `id` should be a persistent track ID**, so an object keeps identity
  across frames. A source annotation UUID is ideal.
- **Attach metadata instead of baking text pixels.** The inspector shows an
  entity's `label` plus any `KeyValuePair` metadata when clicked.
- **Static overlays persist.** A `SceneUpdate` entity stays visible until
  replaced or deleted, so a full-session trajectory polyline can be logged once as
  a `LinePrimitive` with `type=LineStrip`.
- **A `lifetime` on a `SceneEntity`** (for example 150 ms) makes per-frame boxes
  disappear cleanly between updates.
- **Mirror the source devkit's own filtering.** One devkit always drops boxes
  with zero supporting lidar points before display, and skips boxes behind the
  camera before projecting.

See also [§4.5](#45-semantic-and-label-coloring) for sharing one class-color map
across every overlay type.

---

## 6. Timestamps and clock domains

### 6.1 `log_time` vs `header.stamp`

The viewer's shared timeline uses `log_time`, the recording or host clock.
`header.stamp` is the sensor capture clock and can differ per topic in the same
file.

One dataset made this concrete: every message shared one `log_time` domain, but
the stereo camera's `header.stamp` was on the host clock while the lidar and the
ground-truth trajectories were on the sensor's own clock, about 1.7×10⁸ s apart.
So playback was correctly synchronized out of the box, and benchmarking against
ground truth was not. Record the offset as a sample field and say which clock
each product uses.

### 6.2 Nanoseconds since the Unix epoch, everywhere

Convert centrally, in one helper, and watch the source units: microseconds,
seconds-as-float (common for GPS time), separate `secs`/`nsecs` columns,
nanoseconds embedded in a filename, or seconds relative to a sequence start.

```python
def ts(ns: int) -> Timestamp:
    ns = int(ns)
    return Timestamp(sec=ns // 1_000_000_000, nsec=ns % 1_000_000_000)
```

For a clock that counts from sequence start, rebase onto epoch nanoseconds using
the dataset's own start-time metadata. Read a naive local timestamp as UTC so the
same input always yields the same absolute clock; only its consistency across
channels matters for playback:

```python
from datetime import datetime, timezone

def epoch_ns_for(start_time):
    dt = datetime.fromisoformat(start_time).replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)
```

### 6.3 When no real timestamps exist

One archive stored no per-scan capture time, only a sequential index. `t0` was
parsed from the scene folder name and scans were spaced at an assumed 10 Hz. That
is fine for smooth playback, but it must be labeled as an approximation in the
code, the notes, and the dataset card.

The same risk decided a different import's whole strategy: exploded per-frame
files shipped with no timestamp sidecar, so authoring from them would have relied
on nominal rates with real drift risk over a multi-minute sequence. Converting
the original bag, which carried true per-message timestamps, was the safer path.

### 6.4 Conventions differ between sequences of the same dataset

In one dataset, sequence A's `.bin` filenames were GPS-time-of-week in
nanoseconds, while sequence D's were a sequential index with the real per-scan
time in a sibling text file. Detect rather than assume:

```python
import glob, os

def load_lidar_timestamps(data_root, bin_paths):
    """Returns a t_ns array aligned 1:1 with sorted bin_paths."""
    sidecar = glob.glob(os.path.join(data_root, "*LidarScanTimestamp*"))
    if sidecar:
        with open(sidecar[0]) as f:
            secs = [float(x) for x in f.read().split()]
        if len(secs) != len(bin_paths):
            raise ValueError(f"{sidecar[0]}: {len(secs)} timestamps != {len(bin_paths)} files")
        return np.array([int(round(s * 1e9)) for s in secs], dtype=np.int64)
    return np.array([int(os.path.splitext(os.path.basename(p))[0]) for p in bin_paths],
                    dtype=np.int64)
```

### 6.5 Units, especially for GPS

One dataset's GPS CSV stored latitude, longitude, and heading in radians (raw
`lat=0.764, lon=-1.387` is 43.78° N, 79.47° W). `LocationFix` wants degrees for
latitude and longitude, while `heading` is already radians and passes through.
Getting this wrong yields an empty or nonsense Map tile with no error.

```python
latitude=float(np.degrees(float(row["latitude"]))),
longitude=float(np.degrees(float(row["longitude"]))),
altitude=float(row["altitude"]),
heading=float(row["heading"]),          # already radians
```

Available columns can vary by recording era within one dataset: newer sequences
used a `GPSTime` column and included latitude and longitude, while an older one
used `ROSTime` and had neither. Detect and skip rather than assume.

Watch for **all-zero rows instead of omitted rows**. One dataset ships a sequence
with no GPS lock as full rows of zeros with `fix = -1`, so trusting a
`n_gps_fixes` count produces hundreds of fixes at null island.

### 6.6 Rebasing when merging sources

Post-processed bags often carry `ros::Time::now()` from when the offline
processing job ran, weeks after capture. Merged naively, the episode nominally
spans that whole gap and cannot be scrubbed.

```python
offset = anchor_reader.start_time - other_reader.start_time
# add `offset` to every message timestamp from the non-anchor source
```

Validate afterwards: the merged span must be close to the real recording
duration. A single constant offset assumes the source's internal pacing matches,
so if the merged duration is still wrong, per-message header stamps are needed.
See [MCAP-AUTHORING.md](MCAP-AUTHORING.md#appendix-a-complete-ros-1-two-bag-merge)
for the full merge pipeline this fits into.

### 6.7 Real gaps that look like bugs but aren't

- A 2633 s recording where the first real message on any of 110 topics did not
  appear until 101.13 s in. Real recording-startup delay, so the nominal duration
  overstated active data by about 3.5 minutes.
- A sequence where the camera and lidar spanned the first 630 s while the IMU and
  GPS spanned the full 1296 s. Verified real: the camera and lidar stopped while
  the INS kept logging. Do not "fix" this by truncating IMU and GPS to match.
- Message-rate bursts at mode transitions that existed in the original source at
  the same timestamps, verified before and after splitting.
- **Streams that start before the rig clock zero.** One platform's robot topics
  began at -9.7 s. Negative timestamps have to be dropped, or the episode
  overshoots its declared duration.

This is also the explanation if you scrub to the very start of playback and a
tile shows nothing, or "No message at or before the playhead on this topic" —
that topic's first message may genuinely not start at `t=0`. Scrub forward
before concluding a tile is broken; see
[MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#tile-verification-is-a-human-step-and-it-is-not-optional).

### 6.8 Assert monotonic `log_time` per channel

Cheap, and it catches ordering bugs from interleaving multiple sources. The check
is in [MCAP-DATASET-AND-VALIDATION.md](MCAP-DATASET-AND-VALIDATION.md#structural-validation-of-an-authored-episode).
