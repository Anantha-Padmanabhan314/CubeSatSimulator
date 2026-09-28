# CubeSat Simulator — Developer & User Guide

This is a comprehensive reference for the **CubeSat Spacecraft Simulation Framework** in this
repository: what it does, how it's put together, how to run it, and how to extend it. It
complements the auto-generated Sphinx API docs under `docs/source/` (built from Python
docstrings) with an explanation of the *architecture and reasoning* that isn't visible from
any single file.

---

## 1. What this project is

A desktop Python application that simulates a CubeSat (or small satellite) mission:

- High-fidelity **orbit propagation** using [Orekit](https://www.orekit.org/) (a Java
  astrodynamics library, accessed from Python via [JPype](https://jpype.readthedocs.io/)).
- A simplified **rigid-body attitude propagator** (quaternion + angular velocity, RK4
  integration) driven by ADCS torques.
- Six **subsystem models** — EPS (power), ADCS (attitude), Comms, Structure, Payload
  (electrodynamic tether), and Ground (station contacts) — that consume state each timestep
  and produce their own time-series data.
- A **PySide6/Qt GUI** with a 3D Earth/orbit view (PyVista/VTK), a 3D attitude viewer, ground
  track maps (Cartopy), SatNOGS ground-station browsing, per-subsystem config editors, and
  Matplotlib trend plots.
- A **two-process architecture**: the GUI runs in one OS process, the Orekit/JVM-backed
  simulation runs in another, communicating over `multiprocessing.Queue`s.

It's explicitly a teaching/prototyping framework — the README calls it "a starting point for
building educational space mission analysis scenarios" — so several subsystem models are
intentionally simple stand-ins (e.g. ADCS applies zero torque, Structure has no thermal model)
that are meant to be extended.

---

## 2. Repository layout

```
CubeSatSimulator-main/
├── simulator/
│   ├── main.py                 # Entry point: spawns GUI + simulation processes
│   ├── __main__.py             # `python -m simulator` entry point
│   ├── Message.py              # Inter-process message envelope + MessageType enum
│   ├── FrameVector.py          # A vector/point lazily expressed in ECI/ECEF/LVLH/Body
│   ├── FrameTransforms.py      # Rotation matrices between those frames for one instant
│   │
│   ├── model/                  # Simulation logic (no Qt dependency)
│   │   ├── JvmUtilities.py         # Starts the JVM, loads Orekit jars/data
│   │   ├── ModelController.py      # run_simulator(): builds CubeSat, runs propagation
│   │   ├── ModelConfig.py          # Config class + get_default_config()
│   │   ├── CubeSat.py              # The satellite: orbit, attitude, subsystems, step()
│   │   ├── AttitudePropagator.py   # RK4 rigid-body attitude integrator + LVLH conversion
│   │   ├── SimulationStepHandler.py# Orekit fixed-step callback -> CubeSat.step()
│   │   ├── IlluminationCalculator.py # Sun-visibility fraction (eclipse/penumbra geometry)
│   │   ├── DataStore.py            # Time-series storage + CSV export
│   │   ├── Utilities.py            # Date parsing, quaternion/omega math helpers
│   │   │
│   │   └── subsystems/
│   │       ├── Subsystem.py            # Base class: mass/power/data-rate + update()
│   │       ├── eps/                    # Electrical Power System
│   │       │   ├── EpsSubsystem.py, EpsConfig.py, Battery.py, SolarPanel.py
│   │       ├── adcs/                   # Attitude Determination & Control
│   │       │   ├── AdcsSubsystem.py, AdcsConfig.py
│   │       ├── comms/                  # Communications / data downlink
│   │       │   ├── CommsSubsystem.py, CommsConfig.py
│   │       ├── structure/              # Mass properties, drag, inertia
│   │       │   ├── StructureSubsystem.py, StructureConfig.py
│   │       ├── payload/                # Electrodynamic tether payload
│   │       │   ├── PayloadSubsystem.py, PayloadConfig.py, TetherForceModel.py
│   │       └── ground/                 # Ground station visibility/contacts
│   │           ├── GroundSubsystem.py, GroundConfig.py
│   │
│   └── ui/                     # PySide6 GUI (imports from model/, never the reverse)
│       ├── MainDisplayPanel.py     # Root widget: tabs for each subsystem + status bar
│       ├── ControlAndStatusPanel.py# Play/Load/Save, mission name/date/duration, progress
│       ├── SpacecraftPanel.py      # Globe + Attitude + generic config/plot sub-tabs
│       ├── GlobePanel.py           # 3D Earth, orbit path, vector-field heatmaps (PyVista)
│       ├── AttitudePanel.py        # 3D CubeSat model animated through attitude history
│       ├── SubsystemPanel.py       # Generic reusable "config fields + plots" panel
│       ├── GroundPanel.py          # Wraps GroundTrackPanel + SatNOGSPanel in tabs
│       ├── GroundTrackPanel.py     # Cartopy world map with ground track + station marks
│       ├── SatnogsPanel.py         # SatNOGS API browser, drag/drop station selection
│       ├── StationMap.py           # Clickable world map for picking ground stations
│       ├── ConfigFileChooser.py    # Save/Load Config objects as pickle files
│       ├── LogPanel.py             # Scrolling log of simulation status messages
│       ├── NotesPanel.py           # Per-subsystem Markdown notes editor + preview
│       └── MplCanvas.py            # Matplotlib canvas + nav toolbar wrapper widget
│
├── resources/
│   └── 3UCubeSat.ply            # 3D mesh used in the Attitude panel
├── docs/                        # Sphinx documentation project (this file lives here too)
├── install.sh                   # Creates venv, installs deps, checks Java/Orekit setup
├── run.sh                       # Launches the app using the venv
├── requirements.txt
└── README.md
```

Import direction is one-way: `simulator/ui` imports from `simulator/model`, never the other way
around. `simulator/model` never imports PySide6/PyVista. This means the simulation core can in
principle be driven headlessly (see `ModelController.run_simulator`).

---

## 3. Process architecture

The application deliberately runs as **two OS processes**, started from `simulator/main.py:main()`:

```
                 spawn                              spawn
   main() ──────────────────► GUI process    ◄────────────────► Simulation process
                                (PySide6/Qt,                     (Orekit/JVM via JPype,
                                 PyVista, Matplotlib)              CubeSat model)
                                     │                                   │
                       sim_to_gui_queue (status/log/results) ───────────┘
                       gui_to_sim_queue (start/shutdown cmds) ──────────►
```

Why two processes instead of a background thread?

- **JVM isolation.** Orekit is a Java library; JPype embeds a JVM in the process that calls
  `start_jvm()`. Running it in a separate process keeps a slow/blocking numerical propagation
  from freezing the Qt event loop, and avoids any GIL/JVM interaction issues in the GUI process.
- `multiprocessing.set_start_method('spawn', force=True)` is required for PySide6 to work
  correctly with multiprocessing (fork-based start would inherit partially-initialized Qt/GL
  state).

**Message protocol** (`simulator/Message.py`): `Message(type, data)` with `MessageType`:

| Type | Direction | Payload | Meaning |
|---|---|---|---|
| `CMD_START_SIMULATION` | GUI → Sim | `Config` | Run a simulation with this configuration |
| `CMD_SHUTDOWN_SIMULATOR` | GUI → Sim | — | Stop the simulation process loop |
| `STATUS_LOG_MESSAGE` | Sim → GUI | `str` | Appended to the Log tab / status bar |
| `STATUS_SIMULATION_UPDATE` | Sim → GUI | `int` (step number) | Drives the progress bar |
| `STATUS_SIMULATION_COMPLETE` | Sim → GUI | `DataStore` | Triggers all plots to refresh |

The GUI process polls its inbound queue every 50 ms via a `QTimer` (`MainWindow.check_queue`).
The simulation process loop (`run_simulation_process`) polls every 100 ms and dispatches
`run_simulator(config, queue)` synchronously — the app currently only supports **one
simulation run in flight at a time** (the Play button and controls are disabled during a run,
see `ControlAndStatusPanel.on_play_clicked`).

Closing the main window sends `CMD_SHUTDOWN_SIMULATOR`, and `main()` `.join()`s both processes
before exiting.

---

## 4. Startup and environment dependencies

Getting the app running requires more than `pip install`, because Orekit is a Java library:

1. **Python deps** — `pip install -r requirements.txt` (or `./install.sh`, which also creates
   `.venv`). Key packages: `numpy`, `jpype1==1.5.0`, `PySide6==6.9.3`, `pyvista`+`pyvistaqt`,
   `PySpice`, `Cartopy`, `QtPy==2.4.3`, `certifi`, `Markdown`, `requests`, `scipy`, `matplotlib`.
2. **A JDK** must be installed (`jpype` embeds a real JVM). `install.sh` auto-detects/installs
   one (Homebrew `temurin` cask on macOS, `apt`/`dnf` elsewhere).
3. **Orekit + Hipparchus jar files** must be placed in **`~/Orekit-Jars`** (note the exact
   casing — `simulator/model/JvmUtilities.py:start_jvm()` reads
   `os.path.expanduser("~/Orekit-Jars")` literally, and `run.sh` checks the same path).
   > ⚠️ The top-level `README.md`'s example tree shows a lowercase `orekit-jars/` directory —
   > that's stale relative to the code/`run.sh`/`install.sh`, which all use `~/Orekit-Jars`.
   > Use `~/Orekit-Jars` (capital O and J).
4. **Orekit data** (leap seconds, gravity/geomagnetic models, DE-440 ephemerides, EOP, etc.)
   must be extracted to **`~/orekit-data`** (lowercase — this one *does* match the README).
   `JvmUtilities.init_orekit()` points Orekit's `DataProvidersManager` at this directory.
5. `simulator/model/ModelController.py` calls `start_jvm()` and `init_orekit()` at **import
   time** (module level, not inside a function) — so simply importing `ModelController`
   launches the JVM. This is why the simulation logic lives in a separate process: importing
   it once per process is fine, but it can't be re-imported/re-initialized cleanly.

**Running:**
```bash
./install.sh        # one-time setup (venv, deps, Java, checks for Orekit files)
./run.sh             # launch the GUI
# or, equivalently, once the venv is active:
python -m simulator.main
```
Run from the project root — Orekit data paths and the `resources/` mesh path are resolved
relative to environment/repo location, not the working directory of the shell (mesh loading
in `AttitudePanel` uses a path computed from `__file__`, so that part is robust regardless of
cwd; Orekit data is resolved against `~`, so cwd doesn't matter there either — but keep the
convention from the README to avoid surprises with any future path-relative code).

`JvmUtilities._resolve_jvm_path()` has extra logic (macOS-specific) to avoid picking a stale
JDK: it prefers `/usr/libexec/java_home`'s answer over JPype's own auto-detection, and falls
back to dropping a broken `JAVA_HOME` env var if needed.

---

## 5. The configuration system

`simulator/model/ModelConfig.py` defines `Config`, a plain object holding:

- Top-level: `name`, `start_date` (ISO 8601 UTC string), `duration` (days), `step_size`
  (seconds), `spacecraft_config` (dict, orbital elements + initial attitude).
- One dict per subsystem: `eps_config`, `adcs_config`, `comms_config`, `structure_config`,
  `payload_config`, `ground_config`, plus a `stations` list (selected ground stations).

Every subsystem dict is keyed by a `str`-valued `Enum` (`ConfigType`, `EpsConfigType`,
`AdcsConfigType`, …) whose *value* is the human-readable label shown in the UI, e.g.:

```python
class EpsConfigType(str, Enum):
    SOLAR_PANEL_AREA = "Solar Panel Area (m^2)"
    BATT_CAP = "Battery Capacity (Wh)"
    ...
```

This is the extension point the README refers to under "Configuration": **the UI
auto-generates a config editor from whatever keys exist in a subsystem's config dict** — see
`SubsystemPanel.__init__`, which iterates `config_types` and builds one `QLineEdit` row per
entry, bound bidirectionally to `self.config[config_item]`. So adding a new tunable parameter
to a subsystem is: add an enum member to its `*ConfigType`, add a default value in
`get_default_config()`, and read it in the subsystem's constructor — no UI code required.

`get_default_config()` returns a fully populated `Config` (e.g. 300 km altitude, 80° inclined
orbit, "Demo SAT", 1-day duration, 60 s step). This is what `MainWindow` loads at startup.

**Save/Load** (`ConfigFileChooser`): `Config` objects are serialized with `pickle` to `.pkl`
files chosen via a `QFileDialog`. Loading replaces the in-memory config and re-syncs all UI
fields (`MainDisplayPanel.update_config`) including moving ground stations between the
"available"/"selected" lists in the SatNOGS panel.

---

## 6. Simulation core

### 6.1 Entry point

`ModelController.run_simulator(config, msg_queue)`:
```python
cubesat = CubeSat(msg_queue, config)
cubesat.run_simulation(StepHandler(cubesat), config.step_size)
msg_queue.put(Message(MessageType.STATUS_SIMULATION_COMPLETE))
```

### 6.2 `CubeSat` (simulator/model/CubeSat.py)

The top-level object for one simulation run. Constructor responsibilities:
- Parses `start_date`/computes `end_date` from `duration`.
- Builds Orekit frames/bodies: ITRF (Earth-fixed), a WGS84 `OneAxisEllipsoid`, the Sun
  (`CelestialBodyFactory`), and an IGRF-2020 geomagnetic field model.
- Instantiates all six subsystems (`eps`, `adcs`, `comms`, `structure`, `payload`, `ground`),
  passing each its slice of `Config` plus a back-reference to the `CubeSat` itself (so
  subsystems can read cross-subsystem state, e.g. Comms checks `cubesat.ground.ground_contact`).
- Builds the **initial orbit** as a Keplerian orbit (altitude/eccentricity/inclination/
  argument of periapsis/RAAN/mean anomaly from config) in the EME2000 frame.
- Builds the **inertia tensor** from the Structure subsystem's Ixx/Iyy/Izz and constructs an
  `AttitudePropagator` seeded with the configured initial quaternion/angular rate.
- Creates a `DataStore` for time-series recording.

`run_simulation(step_handler, step_size)`:
1. Converts the Keplerian orbit to **Equinoctial** elements (numerically better-conditioned
   for propagation, especially near-circular/near-equatorial orbits).
2. Builds a `NumericalPropagator` with a `DormandPrince853Integrator` (adaptive-step RK8(5,3))
   and tolerances derived from `NumericalPropagator.tolerances(...)`.
3. Adds force models:
   - **20×20 Earth gravity field** (`HolmesFeatherstoneAttractionModel`).
   - **Atmospheric drag** (Harris-Priester model + isotropic drag coefficient from Structure
     config) — can be disabled via the `drag_enabled` constructor flag (not exposed in the UI).
   - **Electrodynamic tether force** (`TetherForceModel`, see §7.5) — always added.
4. Registers `step_handler` on the propagator's step multiplexer at the configured cadence.
5. Propagates from `start_date` to `end_date`, then posts `STATUS_SIMULATION_COMPLETE` with
   the populated `DataStore`, and **writes `../output.csv`** (relative to the process's
   working directory — a hardcoded path; see Known quirks below).

### 6.3 Per-step update — `CubeSat.step(current_state)`

Called once per configured `step_size` (see §6.4 for exactly when). For each step it:
1. Pulls ECI/ECEF position, velocity, acceleration out of Orekit's `SpacecraftState` and
   converts to NumPy via `Utilities.to_array`.
2. Advances attitude with `AttitudePropagator.step(...)`, using the *current* ADCS torque
   command and the elapsed `dt` since the last step, producing body↔ECI and body↔LVLH
   quaternions/RPY.
3. Builds a `FrameTransforms` object for this instant (body→ECI rotation, ECI→ECEF rotation,
   position/velocity) — this is what lets any `FrameVector` (see §6.6) lazily convert between
   frames.
4. Computes Sun direction (ECI), Earth magnetic field at the spacecraft position (via IGRF,
   see `get_mag_field`), nadir direction, illumination fraction (eclipse geometry), and the
   sub-satellite geodetic point.
5. Wraps position/velocity/acceleration/mag-field/nadir/sun-direction as `FrameVector`s.
6. Calls `subsystem.update(dt, current_state)` on every subsystem, **in this fixed order**:
   `eps → adcs → comms → structure → payload → ground`. Order matters: e.g. Comms reads
   `ground.ground_contact` from the *previous* step's `update()` call (Ground hasn't run yet
   this step), and EPS's power balance is computed from every other subsystem's power draw
   for this step.
7. Calls `record_data()`, appending a full row of spacecraft-level scalars/vectors into
   `data_store.spacecraft_data` / `time_data`. (Per-subsystem quantities are recorded inside
   each subsystem's own `update()`.)

### 6.4 `SimulationStepHandler.StepHandler`

Implements Orekit's `OrekitFixedStepHandler` Java interface directly (`@JImplements`), so
Orekit calls back into Python at each fixed-step multiple of `step_size` seconds of simulated
time (not wall-clock time — propagation can run faster or slower than real time depending on
integrator work per step).
- `init(s0, t, step)` — records the step size and initial date.
- `handleStep(current_state)` — guards against calling `CubeSat.step` more than once for the
  same instant, then every 50 steps posts a `STATUS_SIMULATION_UPDATE` progress message.
- `finish(finalState)` — posts a final progress update.

### 6.5 `AttitudePropagator` (simulator/model/AttitudePropagator.py)

A self-contained rigid-body attitude simulator, independent of Orekit's own attitude
providers:
- State: quaternion `q` (scalar-first convention `[w,x,y,z]` is implied by the RK4 code, but
  note `SolarPanel.power()` instead expects **scalar-last** `(x,y,z,w)` for `scipy`'s
  `Rotation.from_quat` — see §8 Known quirks) and body-frame angular velocity `w`.
- `dynamics(q, w, tau)`: standard rigid-body Euler equations,
  `ẇ = I⁻¹(τ − ω × Iω)`, `q̇ = ½ Ω(ω) q`.
- `step(...)` performs **4th-order Runge-Kutta** integration of `[q, w]` over `dt`, assuming
  constant torque `tau` across the step, renormalizes `q`, derives roll/pitch/yaw, and also
  computes the **body→LVLH** quaternion/RPY via `body_to_lvlh_orekit` — which builds an Orekit
  `LocalOrbitalFrame` (LVLH type) from the spacecraft's ECEF position/velocity, extracts its
  rotation to ECI, and composes it with the body→ECI rotation.
- Module-level helper functions (`rotmat_from_quat`, `rotmat_to_quat`, `rotmat_to_rpy`)
  implement standard quaternion↔matrix↔Euler conversions used throughout the attitude code
  and the `AttitudePanel` 3D viewer.

### 6.6 Frame handling — `FrameVector` / `FrameTransforms`

Rather than compute a quantity (position, velocity, magnetic field, nadir, tether force, …)
in every coordinate frame the UI might want to plot it in, the code represents each quantity
as a `FrameVector`: a small lazily-evaluated container holding *at most one* frame's
components plus a shared `FrameTransforms` instance for that instant. Accessing `.eci`,
`.ecef`, `.lvlh`, or `.body` computes and caches the conversion on first access. This is what
lets, e.g., `AttitudePanel` request `.lvlh` for a vector that was only ever populated with
`.eci` data at record time.

`FrameTransforms` (built fresh every `CubeSat.step()` call) holds the rotation matrices for
that instant:
- ECI ↔ ECEF (from Orekit's `Frame.getTransformTo`)
- ECI ↔ Body (from the just-propagated attitude quaternion)
- ECI ↔ LVLH (computed directly from position/velocity: radial/along-track/cross-track basis)

### 6.7 `IlluminationCalculator`

Computes the **fraction of the Sun's disk visible** from the spacecraft (0 = full umbra, 1 =
full sunlight, in between = penumbra), using the classic two-circle-overlap geometry: angular
radii of Sun and Earth as seen from the spacecraft, angular separation between their centers,
and (if partially overlapping) the area of intersection of the two circles. Used to scale
`SolarPanel` power generation and light intensity in the 3D attitude viewer.

### 6.8 `DataStore` (simulator/model/DataStore.py)

A plain container of `{EnumType: [values...]}` dicts, one per subsystem plus spacecraft/time,
appended to every step. `export_single_csv(filename)` merges every dict into one long-format
CSV — one row per signal (name + all its samples), skipping signals that are entirely
empty/zero. This is called automatically at the end of every run, writing to
**`../output.csv`** relative to wherever the simulation process's CWD happens to be (see
Known quirks).

---

## 7. Subsystems

All subsystems derive from `simulator/model/subsystems/Subsystem.py`, which provides:
- `name`, `mass`, `power`, `data_generation_rate` (defaults, overridable per-subsystem)
- `update(dt, state)` — no-op by default, overridden per subsystem
- `get_power_draw()`, `get_mass()`, `get_data_generation_rate()` — default to the static
  attributes above; subsystems override these when the value is dynamic (e.g. Comms only
  draws its higher "transmitting" power while in ground contact).

Every subsystem constructor takes `(cubesat, <subsystem>_config)` and reads its parameters
out of the config dict by the subsystem's `*ConfigType` enum keys.

### 7.1 EPS (Electrical Power System) — `eps/`

- **`EpsSubsystem`**: owns 8 `SolarPanel`s (2 per ±X/±Y body face — note there is **no Z-face
  panel**, so no power is generated with the sun along body Z) and one `BatteryModel`. Each
  step: sums generated watts across all panels, sums power draw across *all* subsystems
  (including EPS's own static draw), computes `net_load = load − generation`, and steps the
  battery by that net power over `dt`. Records per-panel power, battery SOC, and bus voltage.
- **`SolarPanel`** (`SolarPanel.py`): a flat panel with a body-frame normal vector, area,
  efficiency (default 0.28), and solar constant (1361 W/m²). `power(q_body_to_inertial,
  sun_vector_inertial, illumination)` rotates the panel normal into inertial frame with
  `scipy.spatial.transform.Rotation`, takes `cos(incidence angle)` against the sun vector
  (clamped to 0 if facing away), and scales by `illumination` (0–1 from
  `IlluminationCalculator`).
- **`BatteryModel`** (`Battery.py`): energy-based (Wh) battery with **separate
  charge/discharge OCV-vs-SOC curves** (21-point lookup tables, linear interpolation),
  nominal 12 V bus (constructor arg from `EpsSubsystem`, though the interpolation tables are
  themselves scaled ~3.0–4.2 V, i.e. single-cell Li-ion-like values — worth checking/adjusting
  the tables for your actual battery pack voltage). `step(power_W, dt_s)`: positive
  `power_W` discharges, negative charges; energy is clamped to `[0, capacity_Wh]` (no
  over-charge/over-discharge protection modeling beyond the clamp, no low-voltage cutoff
  behavior). `get_voltage()` returns the discharge curve's voltage or charge curve's voltage
  depending on the sign of the *most recent* step.

### 7.2 ADCS (Attitude Determination & Control) — `adcs/`

- **`AdcsSubsystem`**: currently a stub — `self.torque = [0, 0, 0]` always, and `update()` is
  a no-op (`pass`). Config already defines reaction-wheel parameters (inertia, max speed, max
  acceleration, efficiency, idle power coefficient) and `AdcsDataType` already reserves
  roll/pitch/yaw and 4 wheel-speed data series — these are **not yet wired up**. This is the
  most obvious "extend me" subsystem: a real implementation would compute a commanded torque
  (e.g. a PID controller tracking nadir-pointing or sun-pointing) each step and set
  `self.torque`, which `CubeSat.step()` already feeds into `AttitudePropagator.step()`.

### 7.3 Comms — `comms/`

- **`CommsSubsystem`**: models a simple store-and-forward data budget. Each step, it
  increments `data_buffer_bits` by the sum of every subsystem's `get_data_generation_rate() *
  dt` (bits/sec × seconds); if `cubesat.ground.ground_contact` is true, it drains the buffer
  at `tx_datarate * dt`, capped at `data_storage_capacity`. `get_power_draw()` returns the
  higher "transmitting" power figure while in ground contact, otherwise the base power. No RF
  link-budget/margin modeling yet (README explicitly flags this as a future extension).

### 7.4 Structure — `structure/`

- **`StructureSubsystem`**: holds mass, drag area/coefficient (used by `CubeSat`'s drag force
  model) and principal moments of inertia Ixx/Iyy/Izz (used to build the attitude inertia
  tensor) and the 3D mesh filename used by `AttitudePanel`. Its `update()` doesn't compute
  anything new — it just **records** the attitude data (`Q_ECI`, `RPY_ECI`, `Q_LVLH`,
  `RPY_LVLH`) that `CubeSat.step()` already computed, into the data store. (A `StructureDataType.TEMPERATURE` type exists but nothing populates it yet — another
  stubbed extension point.)

### 7.5 Payload — `payload/` (electrodynamic tether)

- **`PayloadSubsystem`**: models a **conducting tether payload** (e.g. an electrodynamic
  tether mission concept). Each step it computes the Lorentz-like tether force
  `F = I·L·(n̂_nadir × B̂)` (cross product of nadir direction and local magnetic field,
  scaled by tether current and length) and records it as a `FrameVector`.
- **`TetherForceModel`** (`TetherForceModel.py`): a **custom Orekit `ForceModel`**
  implemented in Python via JPype's `@JImplements("org.orekit.forces.ForceModel")` — this is
  the one place the simulator extends Orekit's own physics rather than just reading its
  output. It's added to the numerical propagator in `CubeSat.run_simulation()` *unconditionally*
  (not gated on `payload.operational`), so it perturbs the orbit itself: it computes the IGRF
  magnetic field at the spacecraft's position each integrator sub-step, crosses it with the
  nadir direction and scales by `current × length / mass` to get an acceleration, which Orekit
  adds into the equations of motion. `PayloadSubsystem.operational` and `capture()` exist but
  are currently unused stubs.

### 7.6 Ground — `ground/`

- **`GroundSubsystem`**: builds an Orekit `TopocentricFrame` for every selected ground
  station (from `config.stations`, a list of `{name, lat, lng, altitude}` dicts). Each step,
  computes the spacecraft's elevation angle above each station's horizon; `ground_contact` is
  true if **any** station sees the satellite above a **5° elevation mask**. Also records the
  sub-satellite (nadir) latitude/longitude used for the ground track plot.
- Ground station data itself comes from the live **SatNOGS Network API**
  (`https://network.satnogs.org/api/stations/`), fetched by the UI's `SatnogsPanel` (not by
  the model) — the model only ever sees whatever station dicts ended up in `config.stations`
  at Play-button time.

---

## 8. The GUI layer

### 8.1 Window & process glue — `main.py`

`MainWindow` owns the two multiprocessing queues, builds `MainDisplayPanel`, and polls
`msg_queue_in` every 50 ms via `QTimer`, dispatching by `MessageType` (see §3's table).
`main.py` also applies a **Fusion dark theme** (`set_dark_theme`) and synthesizes an emoji
(🛰️) as the window/dock icon (`create_emoji_icon`) rather than shipping an image asset.

### 8.2 `MainDisplayPanel` — the root widget

A `QVBoxLayout` with a `QTabWidget` (stretch=1) on top and `ControlAndStatusPanel` pinned to
the bottom. Tabs, in order: **Spacecraft, EPS, ADCS, Comms, Structure, Payload, Ground, Log**.
Each subsystem tab except Spacecraft/Ground/Log is a generic `SubsystemPanel` (see §8.4).
`update_results(data_store)` fans a completed run's `DataStore` out to every panel's
`update_plots(...)`; `update_config(config)` fans a freshly loaded `Config` out to every
panel's `update_config(...)`.

### 8.3 `ControlAndStatusPanel` — the footer / mission controls

Play (▶️) / Load (📂) / Save (💾) buttons, mission name field, a `QDateTimeEdit` for start
date/time (stored back into `config.start_date` as an ISO 8601 UTC string), duration (days)
and step size (s) fields, a progress bar, and a status label (also mirrors into the Log tab).

- **Play**: disables the run controls, sets the progress bar's max from
  `duration*86400/step_size`, snapshots the currently-selected ground stations from the
  SatNOGS panel into `config.stations`, and posts `CMD_START_SIMULATION`. Controls are
  re-enabled by `MainWindow.handle_message` on `STATUS_SIMULATION_COMPLETE`.
- **Load/Save**: delegates to `ConfigFileChooser` (pickle-based, see §5), and additionally
  reconciles the SatNOGS "available"/"selected" station lists against the loaded config so the
  station picker UI reflects what's actually configured.

### 8.4 `SubsystemPanel` — the generic reusable panel

Used for EPS/ADCS/Comms/Structure/Payload/Spacecraft. Left side: one Matplotlib tab per
`DataType` enum member (auto-built from whatever `*DataType` enum you pass in), right side:
a "Config" tab (one text field per `*ConfigType` enum member, live-bound to the config dict —
values are parsed as `float` on edit) and a "Notes" tab (`NotesPanel`, Markdown editor +
rendered preview, persisted into the config dict under `NotesType.NOTES`). This is the
generic machinery the README refers to under "Extending the Framework" — a brand-new
subsystem with its own `*ConfigType`/`*DataType` enums gets a working config-editor and
trend-plot UI for free by reusing `SubsystemPanel`.

### 8.5 `SpacecraftPanel`

A tab container specific to spacecraft-level (rather than per-subsystem) views:
- **"Orbit and Vector Fields"** → `GlobePanel`
- **"Spacecraft Attitude"** → `AttitudePanel`
- **"Spacecraft Config and Data"** → a generic `SubsystemPanel` bound to `ConfigType`/
  `SpacecraftDataType` (orbital elements + initial attitude config, altitude/inclination/
  eccentricity/illumination/etc. plots)

### 8.6 `GlobePanel` — 3D Earth + orbit + vector fields

A `pyvistaqt.QtInteractor` rendering a textured Earth sphere (`pv.examples.mapfile`), the
propagated orbit path as a polyline, and up to three vector-field overlays plotted as glyph
arrows along the orbit (magnetic field, tether force, nadir direction), each optionally
rendered as a magnitude-colored heatmap (`LinearSegmentedColormap`) instead of flat-colored
arrows. Checkboxes toggle each overlay independently. Note it colors and plots in **ECEF**
frame (`fv.ecef`) — i.e., the Earth-fixed frame, so the Earth mesh doesn't need to rotate to
stay aligned with the orbit/vectors.

### 8.7 `AttitudePanel` — animated 3D attitude viewer

Loads the CubeSat's 3D mesh (`resources/3UCubeSat.ply`, path resolved from `structure_config`)
into a second `QtInteractor`, and after a run completes, animates the mesh through the
recorded attitude history via a `QSlider` + Play/Pause button (25 fps timer). A toggle switches
between showing attitude in the **ECI** frame or the **LVLH** frame. It also positions a
`pv.Light` at the recorded sun direction (intensity scaled by illumination fraction, so the
model visibly darkens in eclipse) and draws velocity (green) and nadir (red) direction arrows.

### 8.8 Ground station UI — `GroundPanel`, `GroundTrackPanel`, `SatnogsPanel`, `StationMap`

- **`GroundTrackPanel`**: a Cartopy `PlateCarree` world map showing the satellite's ground
  track (nadir lat/lon over time), colored **red** during ground contact and **cyan**
  otherwise, with manual line-segmentation logic to avoid drawing spurious lines across the
  antimeridian (±180°) or across contact/no-contact transitions. Selected station locations are
  marked with yellow ✕.
- **`SatnogsPanel`**: fetches the full station list from the live **SatNOGS Network API**
  (`network.satnogs.org`) on panel construction, splits it into "Available" vs "Selected"
  (based on `ground_config[GroundConfigType.STATIONS]`), and presents two paginated,
  band/status-filterable, drag-and-drop list views (`QListView` + custom
  `QAbstractListModel`/delegate that lazy-loads and thumbnails each station's image via a
  background `QThreadPool`). Also embeds a `StationMap` tab for clicking stations directly
  on a world map. Moving a station between lists updates `ground_config[...STATIONS]`
  indirectly (the *canonical* sync back into `Config.stations` only happens in
  `ControlAndStatusPanel.on_play_clicked`/`on_save_clicked`, which read
  `selected_model._all` directly — see §8.3).
- **`StationMap`**: a Cartopy map where clicking a red (available) or green (selected) marker
  toggles that station's membership via a callback into `SatnogsPanel.on_station_clicked`.

### 8.9 Utility panels

- **`LogPanel`**: read-only, auto-scrolling, timestamped text log of every
  `STATUS_LOG_MESSAGE`.
- **`NotesPanel`**: a small Markdown editor/preview pair (uses the `markdown` package with
  `extra`, `tables`, `fenced_code` extensions), embedded per-subsystem via `SubsystemPanel`,
  persisted into that subsystem's config dict.
- **`MplCanvas`/`MplPlotWidget`**: thin wrapper pairing a Matplotlib `FigureCanvasQTAgg` with
  its `NavigationToolbar2QT` (zoom/pan/save) — the building block every plot tab uses.
- **`ConfigFileChooser`**: static save/load helpers around `QFileDialog` + `pickle`
  (see §5).

---

## 9. Typical session, end to end

1. `main()` starts the simulation process (which starts a JVM and loads Orekit data/jars on
   its first import of `ModelController`) and the GUI process.
2. `MainWindow` builds `MainDisplayPanel` from `get_default_config()`; the SatNOGS panel makes
   a live network call to populate the station lists.
3. User edits mission parameters (name/date/duration/step) and subsystem config fields
   directly on the config dicts, optionally selects ground stations by dragging or clicking,
   optionally loads a previously saved `.pkl` config.
4. User clicks ▶️: `ControlAndStatusPanel` snapshots selected stations into
   `config.stations`, posts `CMD_START_SIMULATION`.
5. Simulation process builds a `CubeSat`, runs a `NumericalPropagator` (gravity + drag +
   tether force) from `start_date` to `start_date + duration`, calling `CubeSat.step()` at
   every `step_size`-second boundary via `StepHandler`.
6. Every step: attitude is integrated (RK4), all six subsystems update in fixed order,
   spacecraft-level and subsystem-level time series accumulate in `DataStore`. Progress
   messages stream back to the GUI every 50 steps.
7. On completion: `DataStore` is posted back as `STATUS_SIMULATION_COMPLETE`, exported to
   `../output.csv`, and every panel's `update_plots(...)` is called — trend plots, the 3D
   globe overlays, the ground track, and the attitude animation all populate from the same
   `DataStore`.
8. Controls re-enable; user can rerun with different parameters, or save the current config
   for later reuse.

---

## 10. Extending the framework (per the README's stated extension points)

- **Add a config parameter to an existing subsystem**: add a member to that subsystem's
  `*ConfigType` enum, give it a default in `ModelConfig.get_default_config()`, and read it
  in the subsystem's `__init__`. It appears in the UI automatically via `SubsystemPanel`.
- **Add a new recorded/plotted signal**: add a member to the subsystem's `*DataType` enum,
  append to `cubesat.data_store.<subsystem>_data[YourType]` inside that subsystem's
  `update()`. A plot tab appears automatically.
- **Add real subsystem behavior**: subsystems only need to override `update(dt, state)` (and
  optionally `get_power_draw`/`get_mass`/`get_data_generation_rate` if those become dynamic).
  The most natural first target is **ADCS** (`AdcsSubsystem.update`, currently a no-op) —
  computing `self.torque` there feeds directly into the existing attitude propagator.
- **Add a whole new subsystem**: mirror the structure of an existing one (a `*Config.py` with
  `*ConfigType`/`*DataType` enums, a `*Subsystem.py` subclassing `Subsystem`), wire it into
  `CubeSat.__init__`/`self.subsystems`, add its config dict to `Config`, and add a
  `SubsystemPanel`-based tab in `MainDisplayPanel`.
- **Swap the 3D model**: change `StructureConfigType.MODEL_FILE_3D` (a filename resolved
  against `resources/`).

---

## 11. Known quirks & gotchas (read before you extend or debug)

- **`~/Orekit-Jars` casing**: the code (`JvmUtilities.py`, `run.sh`, `install.sh`) all agree
  on `~/Orekit-Jars`; only the top-level `README.md`'s example tree shows `orekit-jars/`
  (lowercase). Trust the code/scripts.
- **Quaternion component order is inconsistent between two places**: `AttitudePropagator`
  integrates `q = [w, x, y, z]` (scalar-first) and derives RPY assuming that order. But
  `SolarPanel.power()` passes `q_body_to_inertial` straight into `scipy.spatial.transform
  .Rotation.from_quat`, which expects **scalar-last** `[x, y, z, w]`. Since `CubeSat.step()`
  passes `self.q_body_eci` (scalar-first, from `AttitudePropagator`) to `SolarPanel.power` via
  `EpsSubsystem.update`, panel power calculations are rotating by the wrong convention unless
  the initial quaternion happens to be symmetric enough to mask it. Worth double-checking if
  solar power numbers look off after an attitude change — this looks like a real bug rather
  than an intentional design choice, since `CubeSat.__init__` also builds a Hipparchus
  `Rotation(q[0], q[1], q[2], q[3], True)` from the *same* array in a way that (per Hipparchus
  convention) also expects scalar-first, so at minimum these two consumers of `q_body_eci`
  disagree with each other.
- **`output.csv` path is hardcoded and relative**: `CubeSat.run_simulation` always writes to
  `"../output.csv"`, resolved against the simulation process's current working directory at
  runtime (not the project root). Where that file actually lands depends on how you launched
  the app; `run.sh`/`python -m simulator.main` from the project root will write it one level
  above the project root, which may not be where you expect. There's no config option or file
  dialog for this.
- **No EPS +Z/−Z solar panels**: `EpsSubsystem` only mounts panels on the ±X and ±Y faces; a
  spacecraft with its ±Z faces sun-pointing generates zero solar power in this model.
- **Battery voltage curves look single-cell**: `BatteryModel`'s charge/discharge lookup
  tables span ~3.0–4.2 V (typical single Li-ion cell OCV range) while `EpsSubsystem`
  constructs it with `nominal_voltage=12` — that constructor argument is actually unused by
  `get_voltage()` (only the lookup tables matter), so `get_voltage()` currently returns
  single-cell-scale voltages regardless of the configured pack voltage/capacity. Adjust the
  tables (or scale the output) if you need pack-level bus voltage.
- **ADCS applies no torque**: `AdcsSubsystem.torque` is always `[0,0,0]`; the spacecraft only
  ever tumbles freely under its initial angular rate (`W0_0..W0_2` from config) — there is no
  detumbling, pointing control, or reaction-wheel dynamics yet, despite the config/data-type
  enums already anticipating them.
- **Tether force model is always active**: unlike ADCS torque or drag (which has a
  constructor flag), `TetherForceModel` is unconditionally added as a force in
  `CubeSat.run_simulation` — there's no way via the UI/config to disable the tether's orbital
  perturbation even if you don't care about the payload for a given run.
- **One simulation at a time**: the simulation process handles `CMD_START_SIMULATION`
  synchronously in its polling loop; sending a second start command before the first
  completes would queue behind it, but the UI already prevents this by disabling the Play
  button during a run.
- **SatNOGS panel requires network access**: `SatnogsPanel._load_stations()` does a
  synchronous HTTP GET to `network.satnogs.org` at construction time (i.e., at app startup)
  and shows a blocking warning dialog if it fails — there's no offline/cached fallback.
- **`Config.__str__` mislabels some sections**: its docstring/output labels
  `self.eps_config` as `power_config=` in the printed representation — cosmetic only, doesn't
  affect behavior, but can be confusing when reading the Log tab after a Save (which logs
  `str(self.config)`).

---

## 12. Sphinx API docs

`docs/source/*.rst` contains `automodule`/`autoclass` stub files (one per module, generated
via `sphinx-apidoc`) that pull docstrings straight from the source. To build:
```bash
cd docs
make html
```
then open `docs/build/html/index.html`. Must be run with the project importable from the
project root (e.g. with the venv from `install.sh` active) since it imports every module to
extract docstrings — which, per §4, means it will also try to start a JVM and load Orekit
data when it reaches `simulator.model.ModelController`. Make sure `~/Orekit-Jars` and
`~/orekit-data` are in place before running `make html`, or the build will fail on that module.

This guide (`docs/SIMULATOR_GUIDE.md`) is meant to sit alongside those generated API docs as
the "why/how it fits together" companion — the Sphinx docs answer "what does this function
do," this file answers "why does this function exist and what calls it."

---

## 13. License

MIT License, © 2025 Adrian Payne (`avpayne`). See [`LICENSE`](../LICENSE).
