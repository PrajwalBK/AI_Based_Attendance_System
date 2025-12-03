# Setup Instructions for Face Recognition Attendance System

## Problem Summary
When installing dependencies, you may encounter:
- NumPy version compatibility issues
- InsightFace installation errors requiring Microsoft Visual C++ 14.0

## Solution: Step-by-Step Installation

### Step 1: Create and Activate Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate
```

### Step 2: Upgrade pip, setuptools, and wheel

```powershell
python -m pip install --upgrade pip setuptools wheel
```

### Step 3: Install NumPy First (Compatible Version)

```powershell
pip install "numpy>=1.24.0,<2.0.0"
```

### Step 4: Install InsightFace from Local Wheel File

Since you have the pre-built wheel file, install it directly:

```powershell
pip install insightface-0.7.3-cp311-cp311-win_amd64.whl
```

### Step 5: Install Remaining Dependencies

```powershell
# Install opencv-python and other dependencies
pip install opencv-python==4.8.1.78
pip install supervision==0.16.0
pip install onnxruntime==1.16.3
pip install Flask==3.0.0
pip install Flask-Cors==4.0.0
pip install pyttsx3==2.90
pip install Pillow==10.1.0
pip install scikit-learn==1.3.2
```

**OR** use the fixed requirements file (excluding insightface):

```powershell
pip install -r requirements_fixed.txt
```

### Step 6: Verify Installation

```powershell
python -c "import numpy; print('NumPy version:', numpy.__version__)"
python -c "import insightface; print('InsightFace installed successfully')"
python -c "import cv2; print('OpenCV version:', cv2.__version__)"
```

## Alternative: One-Command Installation Script

Create a file called `install_dependencies.bat` and run it:

```batch
@echo off
echo Installing dependencies for Face Recognition Attendance System...

REM Upgrade pip
python -m pip install --upgrade pip setuptools wheel

REM Install NumPy first
pip install "numpy>=1.24.0,<2.0.0"

REM Install InsightFace from local wheel
pip install insightface-0.7.3-cp311-cp311-win_amd64.whl

REM Install other dependencies
pip install opencv-python==4.8.1.78
pip install supervision==0.16.0
pip install onnxruntime==1.16.3
pip install Flask==3.0.0
pip install Flask-Cors==4.0.0
pip install pyttsx3==2.90
pip install Pillow==10.1.0
pip install scikit-learn==1.3.2

echo.
echo Installation complete!
echo.
echo Verifying installations...
python -c "import numpy; print('NumPy version:', numpy.__version__)"
python -c "import insightface; print('InsightFace installed successfully')"
python -c "import cv2; print('OpenCV version:', cv2.__version__)"

pause
```

## Troubleshooting

### If NumPy Still Has Issues:

```powershell
# Uninstall and reinstall NumPy
pip uninstall numpy -y
pip install numpy==1.26.4
```

### If InsightFace Wheel Doesn't Work:

1. **Install Microsoft Visual C++ Build Tools**:
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install "Desktop development with C++" workload

2. **Then try installing from PyPI**:
   ```powershell
   pip install insightface==0.7.3
   ```

### If You Get DLL Load Errors:

```powershell
# Install Microsoft Visual C++ Redistributable
# Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### Check Python Version:

```powershell
python --version
```

Make sure you're using Python 3.11 (since the wheel file is for cp311).

## Clean Installation (If All Else Fails)

```powershell
# Deactivate and remove virtual environment
deactivate
rmdir /s venv

# Create fresh virtual environment
python -m venv venv
.\venv\Scripts\activate

# Follow steps 2-5 above
```

## Running the Application

After successful installation:

```powershell
python main.py
```

## Notes

- The local wheel file `insightface-0.7.3-cp311-cp311-win_amd64.whl` is specifically for Python 3.11 on Windows 64-bit
- If you're using a different Python version, you'll need a different wheel file or build from source
- GPU acceleration requires `onnxruntime-gpu` instead of `onnxruntime`
