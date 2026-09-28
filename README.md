An interactive Earth systems simulation built with Python and PyQt6.

This project models interactions between several parts of the Earth system, including the atmosphere, hydrosphere, geosphere, and biosphere. Users can change environmental conditions and advance the simulation to observe how changes in one system affect other parts of the environment.

Project Screenshot

<!-- Replace the file path below with the location of your screenshot -->



This screenshot shows the graphical user interface used to control and observe the Earth systems simulation.

Overview

The goal of this project is to demonstrate how different Earth systems interact with one another through a graphical simulation.

Instead of treating environmental variables independently, the program uses relationships between temperature, atmospheric pressure, evaporation, precipitation, soil moisture, vegetation, and animal populations to create a simplified dynamic ecosystem.

The project combines a graphical user interface with simulation logic so environmental changes can be viewed interactively.

Features

Interactive graphical user interface built with PyQt6

User-controlled environmental inputs

Air temperature simulation

Water temperature simulation

Surface temperature simulation

Atmospheric pressure calculations

Evaporation modeling

Cloud coverage calculations

Storm probability and intensity

Rain and snow determination

Soil moisture tracking

Flood and drought risk detection

Vegetation health modeling

Plant population growth

Prey population modeling

Predator population modeling

Feedback between environmental and biological systems

Earth Systems Modeled

Atmosphere

The atmosphere portion of the simulation tracks conditions including:

Air temperature

Atmospheric pressure

Cloud coverage

Storm probability

Precipitation type

Changes in temperature can influence atmospheric pressure, evaporation, precipitation, and other environmental conditions.

Hydrosphere

The hydrosphere portion of the simulation models:

Water temperature

Evaporation

Cloud formation

Precipitation

Water temperature and atmospheric conditions influence evaporation, which contributes to cloud formation and weather conditions.

Geosphere

The geosphere portion of the simulation tracks conditions affecting the land, including:

Surface temperature

Soil moisture

Flood risk

Drought risk

Soil moisture changes depending on environmental factors such as precipitation, evaporation, and temperature.

Biosphere

The biosphere models interactions between:

Plants

Prey

Predators

Plant growth is influenced by environmental conditions such as temperature, soil moisture, precipitation, flooding, and drought.

Changes in plant populations affect prey populations, while changes in prey populations influence predator populations.

Simulation Flow

A simplified simulation step follows this process:

User Input
    ↓
Temperature Changes
    ↓
Atmospheric Pressure
    ↓
Evaporation
    ↓
Cloud Formation
    ↓
Storm / Precipitation
    ↓
Soil Moisture
    ↓
Vegetation Health
    ↓
Plant Population
    ↓
Prey Population
    ↓
Predator Population

This allows different systems to influence one another instead of calculating every environmental variable independently.

Technologies Used

Python

PyQt6

Qt Designer

Object-Oriented Programming

Event-Driven Programming

Project Structure

Earth_Project/
│
├── main.py
├── Logic.py
├── Earth_Project.ui
├── screenshots/
│   └── earth_project.png
└── README.md

File Descriptions

main.py
Starts the application and connects the graphical interface to the program.

Logic.py
Contains the main Earth systems simulation logic and calculations.

Earth_Project.ui
Contains the graphical interface designed using Qt Designer.

screenshots/
Stores screenshots used in this README.

Installation

1. Clone the Repository

git clone https://github.com/ColinGable/Earth_Project.git

Move into the project directory:

cd Earth_Project

2. Install PyQt6

python -m pip install PyQt6

3. Generate the Python GUI File

If the project uses the .ui file directly, this step may not be necessary.

Otherwise, convert the Qt Designer file into Python:

pyuic6 Earth_Project.ui -o Earth_Project.py

4. Run the Program

python main.py

Project Purpose

This project was originally developed as an academic Earth science project and gave me the opportunity to apply programming concepts to a real-world scientific system.

While developing the project, I practiced:

Designing graphical applications

Object-oriented programming

Event-driven programming

Separating interface code from program logic

Modeling interacting systems

Translating scientific relationships into code

Managing application state

Creating feedback between multiple simulated systems

Limitations

This program is an educational simulation and is not intended to be used as a scientific forecasting, weather prediction, or climate modeling tool.

The equations and relationships used in the program are simplified representations designed to demonstrate interactions between Earth systems rather than reproduce the full complexity of real-world atmospheric, ecological, or geological systems.

Future Improvements

Possible future additions include:

Graphing environmental variables over time

Saving and loading simulations

More detailed weather systems

Seasonal cycles

Historical simulation data

Improved ecosystem interactions

More advanced scientific models

Adjustable simulation speed

Additional visualization tools

Improved graphical interface
