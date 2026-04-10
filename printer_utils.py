import subprocess
import os
import sys

# Define constant so it works cross-platform safely
CREATE_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)

def get_installed_printers():
    """Returns a list of installed printers, cross-platform."""
    if sys.platform == "win32":
        try:
            cmd = ["powershell", "-Command", "Get-Printer | Select-Object -ExpandProperty Name"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, creationflags=CREATE_NO_WINDOW)
            printers = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            return printers
        except Exception as e:
            print(f"Error fetching Windows printers: {e}")
            return []
    else:
        # macOS/Linux logic
        try:
            result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True, check=True)
            printers = []
            for line in result.stdout.splitlines():
                if line.startswith("printer "):
                    parts = line.split(" ")
                    if len(parts) > 1:
                        printers.append(parts[1])
            return printers
        except Exception as e:
            print(f"Error fetching macOS printers: {e}")
            return []

def get_bundled_sumatra():
    """Returns the path to the bundled SumatraPDF.exe if available."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    sumatra_path = os.path.join(base_path, "SumatraPDF.exe")
    return sumatra_path if os.path.exists(sumatra_path) else None

def print_pdf(filepath, printer_name=None):
    """Submits the PDF to the specified printer with required duplex/collation rules."""
    if sys.platform == "win32":
        sumatra = get_bundled_sumatra()
        if sumatra:
            # SumatraPDF handles bins and duplex natively
            # bin=2 is typical for Tray 2
            settings = "duplexlong,paper=A4,bin=2,color"
            
            p_name = printer_name.strip() if printer_name and printer_name.strip() != "Default Printer" else "default"
            cmd = [sumatra, "-print-to", p_name, "-print-settings", settings, "-silent", filepath]
            
            # Print 3 copies collated manually since Sumatra doesn't have an explicit 'collate 3 copies' param
            # Wait, Sumatra DOES support copies: -print-settings "3x,collate,..."
            settings = "3x,collate,duplexlong,paper=A4,bin=2,color"
            cmd = [sumatra, "-print-to", p_name, "-print-settings", settings, "-silent", filepath]
            
            try:
                subprocess.run(cmd, check=True, creationflags=CREATE_NO_WINDOW)
                return True, "Printed successfully via SumatraPDF"
            except subprocess.CalledProcessError as e:
                return False, f"SumatraPDF Error: {e}"
        else:
            # Fallback if no SumatraPDF: Use default Windows handler via ShellExecute
            try:
                # We do not use win32api as it requires pywin32 to be bundled.
                # Instead we can try to use standard powershell start-process
                p_name = printer_name.strip() if printer_name and printer_name.strip() != "Default Printer" else ""
                if p_name:
                    # In PowerShell, printing to a specific printer using Start-Process is hard without the verb
                    cmd = f'Start-Process -FilePath "{filepath}" -Verb Print'
                else:
                    cmd = f'Start-Process -FilePath "{filepath}" -Verb Print'
                subprocess.run(["powershell", "-Command", cmd], check=True, creationflags=CREATE_NO_WINDOW)
                return True, "Printed via default Windows handler (Note: settings like Tray 2 not enforced)"
            except Exception as e:
                return False, f"Windows Print Error: {e}"
    else:
        # macOS logic
        cmd = [
            "lp",
            "-n", "3",
            "-o", "Collate=True",
            "-o", "sides=two-sided-long-edge",
            "-o", "media=A4",
            "-o", "InputSlot=Tray2",
            "-o", "fit-to-page",
            "-o", "portrait"
        ]
        
        if printer_name and printer_name.strip() != "Default Printer" and printer_name.strip() != "":
            cmd.extend(["-d", printer_name])
            
        cmd.append(filepath)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
