# OPT-SAR Registration Script

This is a script for registering Optical (OPT) and Synthetic Aperture Radar (SAR) images.

## 📁 Directory Structure

Please make sure your files are organized in the following structure before using the script:

dataset/
|
├── OPT/     # Folder containing the optical images
|   ├──
|   └──
├── SAR/     # Folder containing the SAR images
|   ├──
|   └──
|   Label/   # Output folder for the registration results
|   ├──
└── └──

## 🚀 How to Run

You have two options to run this script:

### Option 1: Run the Executable

Navigate to the `dist` folder and double-click the `.exe` file to launch the script.

### Option 2: Run the Python Script

1. Make sure your Python environment is set up.
2. Install the required packages by running:

   ```bash
   pip install -r requirements.txt
3. Then run the main script:

   ```bash
    python OS_tool.py
## 🧭 How to Use

1. Open the script (either the .exe or OS_tool.py).

2. Click “Open Folder” buttons to:

   * Select the OPT folder (optical images).

   * Select the SAR folder (SAR images).

3. Click “Select Save Directory” to choose the Label folder (where results will be saved).

4. Start the registration process by clicking the corresponding button in the interface.

5. Sit back and enjoy — the matched results will be saved in the Label/ folder.

Feel free to open an issue if you encounter any problems or have suggestions for improvements.
