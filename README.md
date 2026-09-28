# 🛰️ QSET CubeSat Spacecraft Simulation Framework

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg)
![Orekit](https://img.shields.io/badge/Orekit-13.x-orange.svg)
![PySide6](https://img.shields.io/badge/PySide6-Qt%20for%20Python-41CD52.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

A Python framework for simulating CubeSats or small spacecraft missions using:

- **[Orekit](https://www.orekit.org/)** – High-precision orbital mechanics
- **[PySide6](https://doc.qt.io/qtforpython/)** – Graphical User Interface
- **[PyVista](https://docs.pyvista.org/)** – 3D visualization and rendering
- **[Hipparchus](https://www.hipparchus.org/index.html)** – Mathematical utilities
- **[PySpice](https://github.com/PySpice-org/PySpice)** – Electrical simulation


---

## ✨ Features

✅ Orbital propagation using Orekit  
✅ 3D Earth + orbit visualization with PyVista  
✅ GUI panels for spacecraft configuration, simulation control and data plotting  
✅ UTC date/time selection and scenario setup tools  
✅ Modular architecture — easy to extend for custom missions  

---

## 📦 Project Structure

```plaintext
project/
│
├── simulator/
│   ├── ui/                 # PySide6 UI & PyVista components and panels
│   ├── model/              # Simulation logic and Orekit integration
│   │   └── subsystems/     # Subsystem models
│   │       ├── adcs/       # ADCS model
│   │       ├── power/      # Power model
│   │       ├── structure/  # Structure model
│   │       ├── comms/      # Comms model
│   │       └── payload/    # Payload model
│   └── main.py             # Application entry point
│
├── resources/              # icons, textures, etc.
└── README.md
```

---

## 🚀 Getting Started

The simulator needs three things besides the code itself:

1. **Python 3.11 or 3.12** with the packages in `requirements.txt`. Python 3.13 won't work yet, because the pinned `jpype1==1.5.0` has no 3.13 build.
2. **A Java JDK, version 17 or newer.** Orekit is a Java library, and Python talks to it through JPype. Eclipse Temurin is a good free choice.
3. **The Orekit jar files and the Orekit data folder**, in your home directory with these exact names:

```plaintext
<your home folder>/
├── Orekit-Jars/                   ← capital O and J; the name is case-sensitive on Linux
│   ├── orekit-13.1.2.jar
│   ├── hipparchus-core-4.0.2.jar
│   ├── hipparchus-filtering-4.0.2.jar
│   ├── hipparchus-fitting-4.0.2.jar
│   ├── hipparchus-geometry-4.0.2.jar
│   ├── hipparchus-ode-4.0.2.jar
│   ├── hipparchus-optim-4.0.2.jar
│   └── hipparchus-stat-4.0.2.jar
└── orekit-data/                   ← all lowercase
    ├── DE-440-ephemerides
    ├── Earth-Orientation-Parameters
    ├── IGRF.COF
    ├── Potential
    └── ... (the rest of the orekit-data repository)
```

Your home folder is `/Users/<name>` on macOS, `/home/<name>` on Linux and `C:\Users\<name>` on Windows. Every `.jar` in `Orekit-Jars` is loaded, so extra Hipparchus jars there are harmless.

Pick your platform below. Every step only has to be done once.

### 🍎 macOS

**1. Get the code and Python**

```bash
git clone <this-repository-url> CubeSatSimulator
cd CubeSatSimulator
brew install python@3.11
```

**2. Run the install script.** It creates a `.venv` virtual environment, installs the Python packages, and installs a JDK through Homebrew if you don't have one.

```bash
PYTHON=python3.11 ./install.sh
```

**3. Download the Orekit jars**

```bash
mkdir -p ~/Orekit-Jars && cd ~/Orekit-Jars
curl -LO https://repo1.maven.org/maven2/org/orekit/orekit/13.1.2/orekit-13.1.2.jar
for m in core geometry ode fitting optim filtering stat; do
  curl -LO https://repo1.maven.org/maven2/org/hipparchus/hipparchus-$m/4.0.2/hipparchus-$m-4.0.2.jar
done
cd -
```

**4. Download the Orekit data**

```bash
git clone https://gitlab.orekit.org/orekit/orekit-data.git ~/orekit-data
```

**5. Run**

```bash
./run.sh
```

### 🐧 Linux (Ubuntu / Debian)

**1. Install the system packages.** `libxcb-cursor0` is needed by Qt to open windows on X11. Without it you get an error saying the "xcb" platform plugin could not be loaded.

```bash
sudo apt update
sudo apt install git python3 python3-venv libxcb-cursor0
```

Ubuntu 24.04 ships Python 3.12, which works. On Ubuntu 22.04, which ships 3.10, install `python3.11 python3.11-venv` as well and use `PYTHON=python3.11` in the next step. On Fedora, use `dnf` with the equivalent package names.

**2. Get the code and run the install script.** If no JDK is found, the script installs OpenJDK 17 with `apt` (or `dnf`) and asks for your password.

```bash
git clone <this-repository-url> CubeSatSimulator
cd CubeSatSimulator
PYTHON=python3 ./install.sh
```

**3. Download the Orekit jars and data.** These are the same commands as on macOS:

```bash
mkdir -p ~/Orekit-Jars && cd ~/Orekit-Jars
curl -LO https://repo1.maven.org/maven2/org/orekit/orekit/13.1.2/orekit-13.1.2.jar
for m in core geometry ode fitting optim filtering stat; do
  curl -LO https://repo1.maven.org/maven2/org/hipparchus/hipparchus-$m/4.0.2/hipparchus-$m-4.0.2.jar
done
cd -
git clone https://gitlab.orekit.org/orekit/orekit-data.git ~/orekit-data
```

**4. Run**

```bash
./run.sh
```

### 🪟 Windows

`install.sh` and `run.sh` are bash scripts, so on Windows the same steps are done by hand in **PowerShell**.

**1. Install Python, Java and Git.** You can use `winget` as shown below, or the installers from python.org, adoptium.net and git-scm.com.

```powershell
winget install Python.Python.3.11
winget install EclipseAdoptium.Temurin.21.JDK
winget install Git.Git
```

Close and reopen PowerShell afterwards so the new programs are on your PATH.

**2. Make sure `JAVA_HOME` is set.** JPype uses it to find Java on Windows.

```powershell
echo $env:JAVA_HOME
```

If that prints nothing, point it at your JDK folder, then reopen PowerShell:

```powershell
setx JAVA_HOME "C:\Program Files\Eclipse Adoptium\jdk-21.0.x-hotspot"
```

Use the actual folder name you see under `C:\Program Files\Eclipse Adoptium\`.

**3. Get the code and install the Python packages**

```powershell
git clone <this-repository-url> CubeSatSimulator
cd CubeSatSimulator
py -3.11 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
```

**4. Download the Orekit jars**

```powershell
New-Item -ItemType Directory -Force "$HOME\Orekit-Jars" | Out-Null
Invoke-WebRequest https://repo1.maven.org/maven2/org/orekit/orekit/13.1.2/orekit-13.1.2.jar -OutFile "$HOME\Orekit-Jars\orekit-13.1.2.jar"
foreach ($m in "core","geometry","ode","fitting","optim","filtering","stat") {
  Invoke-WebRequest "https://repo1.maven.org/maven2/org/hipparchus/hipparchus-$m/4.0.2/hipparchus-$m-4.0.2.jar" -OutFile "$HOME\Orekit-Jars\hipparchus-$m-4.0.2.jar"
}
```

**5. Download the Orekit data**

```powershell
git clone https://gitlab.orekit.org/orekit/orekit-data.git "$HOME\orekit-data"
```

If you'd rather not use Git, download the [orekit-data zip](https://gitlab.orekit.org/orekit/orekit-data/-/archive/main/orekit-data-main.zip), extract it into your home folder, and rename `orekit-data-main` to `orekit-data`.

**6. Run** (from the project folder)

```powershell
.venv\Scripts\python -m simulator.main
```

## 🏁 Running the Simulator

Always start the simulator from the project root folder, so it can find `resources/` and write its results.

| Platform | Command |
|---|---|
| macOS / Linux | `./run.sh` |
| Windows | `.venv\Scripts\python -m simulator.main` |
| Any, with the virtual environment activated | `python -m simulator.main` |

`run.sh` checks that `.venv`, `~/Orekit-Jars` and `~/orekit-data` exist before starting, so it tells you what's missing instead of failing with a Java error.

Once the window is open:

1. Optionally pick ground stations in **Ground → Station Selection**. The list comes from the SatNOGS website, so this needs an internet connection.
2. Adjust any settings in the **Config** part of each tab. The tether settings are under **Payload**.
3. Set the start date, the duration (in days) and the step size (in seconds) in the bar at the bottom, then press **▶**.
4. Watch the progress bar and the **Log** tab. When the run finishes, all the plots fill in, and the results are also written to `../output.csv`, one folder above the project.

For a first check, use a short duration such as 0.1 days.

### Run from PyCharm

1. Open the project folder in PyCharm.
2. Set the project interpreter to the `.venv` created during installation.
3. Create a Run Configuration:
   - **Module name:** `simulator.main`
   - **Working directory:** the project root
4. Click **Run**.

### Troubleshooting

| Problem | Fix |
|---|---|
| `Could not locate a valid Java installation` | Install a JDK (17 or newer). If `JAVA_HOME` is set, check that it points to a folder that actually exists. |
| `No JVM shared library file (jvm.dll) found` (Windows) | Set `JAVA_HOME` as in Windows step 2, then open a new PowerShell. |
| `FileNotFoundError` mentioning `Orekit-Jars` | The jar folder is missing or named differently. It must be `Orekit-Jars` in your home folder, with that exact capitalisation. |
| Orekit errors about missing data, such as UTC-TAI or gravity field files | `~/orekit-data` is missing, empty, or nested one level too deep (e.g. `orekit-data/orekit-data-main/...`). |
| `Could not load the Qt platform plugin "xcb"` (Linux) | `sudo apt install libxcb-cursor0` |
| `pip` fails while building `jpype1` | You're on Python 3.13. Create the virtual environment with Python 3.11 or 3.12 instead. |
| `ModuleNotFoundError` for `PySide6`, `numpy` and so on | You're running the system Python. Use `./run.sh`, or the `.venv` Python as shown above. |

---

## 🧩 Extending the Framework

- **Subsystem Models:** Update subsystem shell classes under `simulator/model/subsystems/`.

---

## 🛠️ Configuration

- **Resources:** Icons, textures, and mesh files are under `resources/`.
- **Subsystem Configurations:** Update the simulator.model.subsystems.<subsystem name>.<SubsystemName>Config.py file to include new configuration items for that subsystem that will automatically be available in the UI
- **Default Configuration:** Update the simulator.model.ModelConfig.py file to reflect default values for new subsystem configuration items
- **Subsystem datastore:** Update the simulator.model.DataStore.py file to reflect data that you want to collect/analyze from the subsystems

---

## 📚 Documentation

Sphinx documentation is provided under the `docs/` folder.

```bash
cd docs
make html
```

- Open `_build/html/index.html` in your browser.
- To include your modules and classes, make sure Python imports work from the project root.

---

## 💡 Tips

- Use a virtual environment to manage dependencies.
- For GUI debugging, run the application with `python -m simulator.main` from the terminal to see full exception traces.

---

## 📖 References

- [Orekit Documentation](https://www.orekit.org/)
- [PySide6 Docs](https://doc.qt.io/qtforpython/)
- [PyVista](https://docs.pyvista.org/)
- [Hipparchus](https://www.hipparchus.org/index.html)
- [PySpice](https://github.com/PySpice-org/PySpice)

---

## 📝 License

MIT License – see [LICENSE](LICENSE) file.

---

## 🌍 The Orbital Simulator

This section is for anyone who needs to change how the satellite moves, what forces act on it, or how results are produced. It explains what actually runs when you press Play, which physical models are used, and which file to open for each part.

### What happens during a run

The application runs as two separate processes that talk to each other through message queues:

1. `main.py` starts a GUI process (PySide6) and a simulation process (Orekit running in a JVM through JPype).
2. When you press Play, `ControlAndStatusPanel` collects the current `Config` and the ground stations selected in the Ground tab, and sends them to the simulation process as a `CMD_START_SIMULATION` message.
3. `ModelController.run_simulator()` builds a `CubeSat` from that config and calls `CubeSat.run_simulation()`.
4. `run_simulation()` sets up the Orekit propagator, adds the force models, and propagates from the start date to the end date.
5. Every `step_size` seconds (60 s by default) Orekit calls `StepHandler.handleStep()`, which calls `CubeSat.step()`. That computes the frame vectors (position, velocity, sun direction, magnetic field, nadir), steps the attitude propagator, calls `update()` on every subsystem and records everything in the `DataStore`.
6. When propagation finishes, the `DataStore` is sent back to the GUI for plotting, and all non-empty series are written to `../output.csv`. The path is relative to the working directory, so running from the project root puts the file one level above the project folder.

### Propagator and integrator

- **Propagator:** Orekit `NumericalPropagator`.
- **Integrator:** Dormand–Prince 8(5,3) (`DormandPrince853Integrator`), an adaptive 8th order Runge Kutta method. The minimum step is 0.001 s and the maximum is 500 s. Tolerances come from `NumericalPropagator.tolerances()` with a 1 m position scale.
- **Orbit representation:** the initial orbit is entered as Keplerian elements in EME2000 and converted to equinoctial elements before integration. Equinoctial elements stay well defined for near circular and near equatorial orbits.
- **Initial orbit:** the semi major axis is the configured altitude plus Earth's equatorial radius (6378.137 km). Eccentricity, inclination, argument of periapsis, RAAN and anomaly come from the Spacecraft config tab.
- **Mass:** the sum of every subsystem's configured mass. It stays constant for the whole run.
- **Reporting vs. integration steps:** the integrator picks its own step size, typically a few minutes in LEO. The 60 s reporting step is independent of it. Orekit interpolates the integrator's solution to each exact reporting time, so the recorded states land on a clean, evenly spaced grid. Making `step_size` smaller gives you more samples; it does not make the orbit more accurate. To make the orbit more accurate, tighten the tolerance scale in `run_simulation()`.

### Environment models

| What | Model | Where it is set up |
|---|---|---|
| Earth shape | WGS84 ellipsoid | `CubeSat.__init__`, also in the tether and ground models |
| Inertial frame | EME2000 | initial orbit in `CubeSat.__init__` |
| Earth-fixed frame | ITRF (IERS 2010 conventions) | used everywhere a latitude, longitude or magnetic field is needed |
| Gravity | Holmes–Featherstone spherical harmonics, degree and order 20 | `run_simulation()`. Coefficients are read from `~/orekit-data/Potential` (EIGEN-6S in the standard Orekit data set) |
| Atmosphere | Harris–Priester density model | `CubeSat.get_drag_force_model()` |
| Magnetic field | IGRF, evaluated at epoch 2020 | `TetherForceModel`, `CubeSat.get_mag_field()` |
| Sun position | Orekit's Sun, from the DE-440 ephemerides | `CubeSat.__init__`, `IlluminationCalculator` |
| Eclipse | Conical shadow with a partial penumbra, computed from the overlap of the Sun and Earth disks | `IlluminationCalculator.compute_fraction()` |
| Ionospheric plasma density | Constant placeholder, 1e11 m⁻³ | `PlasmaDensityModel.get_plasma_density()` |

### Forces acting on the orbit

Three force models are added to the propagator, and Orekit sums their accelerations at every integrator evaluation:

1. **Gravity:** Holmes–Featherstone 20×20, as above.
2. **Atmospheric drag:** Orekit `DragForce` combining Harris–Priester with `IsotropicDrag`. The drag area and drag coefficient come from the Structure config tab, and the drag area doesn't change with attitude. Drag is on by default (`CubeSat(..., drag_enabled=True)`).
3. **Electrodynamic tether force:** `TetherForceModel`. At every evaluation it solves for the tether current and applies F = I·L·(u × B), where u is the tether direction, assumed to point straight down (nadir). See the Payload section below.

To add any forces, add another `propagator.addForceModel(...)` line in `CubeSat.run_simulation()`. Orekit ships ready made classes for all of them.

### Attitude

Attitude is propagated separately from the orbit, and the two are not coupled.

- `AttitudePropagator` integrates Euler's rigid-body equations and quaternion kinematics with a fixed-step RK4. It advances once per reporting step (`dt = step_size`).

- The inertia tensor is diagonal, built from Ixx, Iyy and Izz in the Structure config. The defaults are all equal, so the satellite simply spins at its initial rate.

- The only torque input is `AdcsSubsystem.torque`, which is currently always zero. No gravity gradient, aerodynamic, magnetic or tether torques are computed.

- Attitude affects solar panel power and the 3D attitude display. It does not affect drag or the tether direction.

### Main modules

**Entry point**
- `simulator/main.py`: starts the GUI and simulation processes, applies the dark theme, and routes status messages to the right panels.
- `simulator/__main__.py`: lets you run the app with `python -m simulator`.
- `simulator/Message.py`: the message types and the message class used between the two processes.
- `simulator/model/ModelController.py`: starts the JVM and Orekit, then builds and runs a `CubeSat` for each start command.
- `simulator/model/JvmUtilities.py`: finds a working JDK, starts the JVM with the jars in `~/Orekit-Jars`, and points Orekit at `~/orekit-data`.

**Simulation core**
- `simulator/model/CubeSat.py`: the top level model. It owns the subsystems, sets up the propagator and force models (`run_simulation`), and does the per-step bookkeeping (`step`, `record_data`). Start here for anything orbit-related.
- `simulator/model/SimulationStepHandler.py`: the Orekit fixed step handler that calls `CubeSat.step()` at each reporting time and sends progress updates to the GUI.
- `simulator/model/AttitudePropagator.py`: RK4 rigid body attitude propagation and body->LVLH conversion.
- `simulator/model/IlluminationCalculator.py`: the fraction of the Sun visible from the spacecraft.
- `simulator/model/ModelConfig.py`: the `Config` container, the spacecraft level config keys, and `get_default_config()` with every default value.
- `simulator/model/DataStore.py`: time series storage for every recorded quantity, plus the CSV export.
- `simulator/model/Utilities.py`: date parsing, Java vector to NumPy conversion, and quaternion helpers.

**Frames**
- `simulator/FrameTransforms.py`: rotation matrices between ECI, ECEF, LVLH and body, rebuilt at every step.
- `simulator/FrameVector.py`: a vector that can be read in any of those four frames. It converts lazily, using the step's `FrameTransforms`.

**User interface** (`simulator/ui/`)
- `MainDisplayPanel.py`: the main window layout, with one tab per subsystem plus the status bar.
- `ControlAndStatusPanel.py`: the name, start date, duration and step-size fields, the Play/Load/Save buttons, and the progress bar.
- `SpacecraftPanel.py`: hosts the 3D globe, the attitude view and the spacecraft level plots.
- `GlobePanel.py`: the PyVista 3D globe showing the orbit and toggleable vector fields (magnetic field, tether force, nadir direction) and heatmaps.
- `AttitudePanel.py`: the 3D spacecraft mesh, animated through the recorded attitude history.
- `SubsystemPanel.py`: the generic tab used by each subsystem. It builds the config form and the plot tabs automatically from the subsystem's enums.
- `GroundPanel.py`, `SatnogsPanel.py`, `StationMap.py`, `GroundTrackPanel.py`: SatNOGS ground station browsing and selection (fetched from the SatNOGS network API), and the ground-track map (Cartopy).
- `ConfigFileChooser.py`: saves and loads a `Config` as a pickle file.
- `MplCanvas.py`, `LogPanel.py`, `NotesPanel.py`: the Matplotlib canvas wrapper, the log tab and a free text notes field.

### Known issues

These are worth knowing before you trust a particular output:

- **IGRF is fixed at 2020.** `getIGRF(2020)` ignores the simulation date, so runs in 2026–2027 see a few years of field drift, on the order of 0.5–1%.
- **`TetherForceModel.dependsOnPositionOnly()` returns True**, but the tether force also depends on velocity. This is harmless for plain propagation, but it should be False before using this force model for orbit determination. This is not our concern right now.

---

## 🔧 Subsystems

Every subsystem inherits from `simulator/model/subsystems/Subsystem.py`. The base class holds a mass, a power draw and a data generation rate, and defines `update(dt, state)`, which `CubeSat.step()` calls once per reporting step. Subsystems are updated in this order:

EPS → ADCS → Comms → Structure → Payload → Ground

The order matters. For example, Comms reads the Ground subsystem's contact flag, which was set on the previous step.

Each subsystem folder follows the same pattern:

- `<Name>Config.py` defines two enums. `<Name>ConfigType` lists the inputs, and each entry shows up as an editable field in that subsystem's GUI tab. `<Name>DataType` lists the outputs, and each entry gets its own storage list in the `DataStore` and its own plot tab.
- `<Name>Subsystem.py` reads its config in `__init__`, does its work in `update()`, and appends results to the `DataStore`.

### What is implemented

| Subsystem | Status | What it does |
|---|---|---|
| **EPS** (power) | Working, simplified | Eight body mounted panels, two each on the ±X and ±Y faces. Each produces 1361 W/m² × area × 28% efficiency × cos(incidence) × illumination fraction. The load is the sum of every subsystem's power draw. The battery tracks energy in Wh, clamped between empty and full. |
| **ADCS** | Placeholder | Torque is always zero. The reaction wheel parameters in the config aren't used yet, and the ADCS plot tabs stay empty. |
| **Comms** | Working, simplified | Every subsystem's data rate fills an onboard buffer. During ground contact it drains at the transmit data rate, and the power draw switches to the transmitting value. The buffer is capped at the storage capacity. |
| **Structure** | Parameter holder | Holds the drag area, drag coefficient, inertia and 3D mesh file, and records the attitude history (quaternions and roll/pitch/yaw in ECI and LVLH). Temperature is defined but not modeled. |
| **Payload** | Working | A passive bare electrodynamic tether (EDT). It solves for the tether current from orbital motion, the magnetic field and the plasma, and applies the resulting Lorentz drag to the orbit. |
| **Ground** | Working | Flags contact when the satellite is at least 5° above the horizon at any selected SatNOGS station, and records the sub-satellite latitude and longitude. |

### Payload: the electrodynamic tether

The payload is the most developed subsystem, and the only one that feeds back into the orbit. The tether is modeled as a straight, rigid wire hanging along nadir. It has a bare segment that collects electrons from the plasma, an insulated segment, and an electron emitter at the spacecraft end.

At each evaluation, the motional field E_m = (v × B) · u is computed from the Earth relative velocity and the IGRF field. That field, the plasma density and the tether geometry give a characteristic length L\*, which is used to normalize the problem. A closed form solution of the OML (orbital motion limited) collection equations then gives the average current. The sign of the current follows E_m, which guarantees the force always opposes the motion.

The current is computed in two places, for different reasons:
- the integrator calls it at its own internal times, to apply the force
- `PayloadSubsystem.update()` calls it at each reporting time, for telemetry

Both call the same function, so the physics lives in one place.

Things the tether model does not include yet: realistic plasma density (currently a constant), the emitter's actual voltage drop (currently a fixed config value), ion collection past the zero voltage point, tether swinging (libration) and flexibility, and any torque on the spacecraft.

### Subsystem modules

**Base**
- `subsystems/Subsystem.py`: the base class, with default `get_mass()`, `get_power_draw()` and `get_data_generation_rate()` that subclasses can override.

**EPS** (`subsystems/eps/`)
- `EpsSubsystem.py`: builds the eight panels, sums generation and load each step, and steps the battery. Records panel power, state of charge and bus voltage.
- `SolarPanel.py`: power from a single panel given the attitude, the Sun direction and the illumination fraction.
- `Battery.py`: energy bookkeeping, with voltage looked up from separate charge and discharge curves of a single Li-ion cell (3.0–4.2 V).
- `EpsConfig.py`: EPS inputs (panel area, battery capacity, initial charge and so on) and outputs.

**ADCS** (`subsystems/adcs/`)
- `AdcsSubsystem.py`: exposes the `torque` read by the attitude propagator. Currently always `[0, 0, 0]`. This is where a control law would go.
- `AdcsConfig.py`: ADCS inputs (including the unused reaction wheel parameters) and outputs.

**Comms** (`subsystems/comms/`)
- `CommsSubsystem.py`: data buffer fill and downlink logic, and the transmit/idle power draw.
- `CommsConfig.py`: data rate, storage capacity and power inputs, and the storage output.

**Structure** (`subsystems/structure/`)
- `StructureSubsystem.py`: stores the physical parameters used by drag and attitude, and records the attitude history.
- `StructureConfig.py`: drag area, drag coefficient, mass, principal moments of inertia and mesh file.

**Payload** (`subsystems/payload/`)
- `PayloadSubsystem.py`: reads the tether settings, and at each reporting step records the tether current and force.
- `TetherForceModel.py`: the Orekit force model. `_geometry_and_field()` gets v, u and B in ITRF. `compute_current()` builds the normalized inputs and calls the solver. `acceleration()` returns F/m in the propagation frame.
- `BetClosedFormSolver.py`: the dimensionless closed form solver. `solve_phi_A()` finds the voltage at the tether tip with a single `brentq` root-find, and `average_current()` returns the length averaged current. The Fs integral table is built once, at import.
- `PlasmaDensityModel.py`: the plasma density lookup. It returns a constant for now, and this is the place to plug in a real ionosphere model such as IRI.
- `PayloadConfig.py`: tether inputs (bare and insulated length, conductivity, cross-section area, perimeter, emitter voltage drop) and outputs (`TETHER_FORCE`, `TETHER_CURRENT`).

**Ground** (`subsystems/ground/`)
- `GroundSubsystem.py`: elevation checks against each selected station, the contact flag, and the sub-satellite point.
- `GroundConfig.py`: station list and band filter inputs, and the contact and ground track outputs.

### Adding or changing a subsystem

1. Add inputs to `<Name>ConfigType` and outputs to `<Name>DataType` in the subsystem's config file.
2. Give every new input a default in `get_default_config()` in `ModelConfig.py`. Configs saved before the change won't have the new keys, and loading one will raise a `KeyError`.
3. Read the inputs in the subsystem's `__init__`, and append exactly one value per output in `update()`. Each output list must have the same length as the time list, or the plot will fail.
4. For a brand new subsystem, create it in `CubeSat.__init__`, add it to `self.subsystems`, add a storage dict in `DataStore`, and add a `SubsystemPanel` tab in `MainDisplayPanel`.
5. If the subsystem should affect the orbit, write an Orekit force model (see `TetherForceModel.py` for the JPype pattern) and add it in `CubeSat.run_simulation()`.
