# DNS Switcher for Windows

A simple Python application to change DNS settings on Windows systems.

## Features

- List all available network adapters
- Display current DNS settings for selected adapter
- Change DNS settings for selected network adapter
- Predefined DNS options:
  - Google DNS (8.8.8.8, 8.8.4.4)
  - Cloudflare DNS (1.1.1.1, 1.0.0.1)
  - OpenDNS (208.67.222.222, 208.67.220.220)
  - AliDNS (223.5.5.5, 223.6.6.6) - Chinese DNS provider
  - 114DNS (114.114.114.114, 114.114.115.115) - Chinese DNS provider
- Custom DNS settings
- Reset DNS to automatic (DHCP)
- Graphical User Interface (GUI) version available
- **New**: Refresh network adapter list button in GUI version
- **New**: Reselect network adapter option in CLI version


## Requirements

- Windows operating system
- Python 3.x
- **Administrator privileges (REQUIRED for modifying DNS settings)**

## Usage

### Console Version

#### Method 1: Using the Batch File (Recommended)

1. Double-click on `run_dns_switcher.bat` (the batch file will automatically request administrator privileges)

#### Method 2: Using Command Line

1. **IMPORTANT**: Right-click on the command prompt or PowerShell and select "Run as administrator"

2. Run the script:
   ```
   python dns_switcher.py
   ```

3. Select a network adapter from the list

4. Choose a DNS option from the menu (options 1-7)

5. **New**: Option 8 allows you to re-select network adapter without restarting the program

6. Option 9 to exit the program

### GUI Version

#### Method 1: Using the Batch File (Recommended)

1. Double-click on `run_gui_as_admin.bat` (the batch file will automatically request administrator privileges, manage logs, and provide user feedback)

#### Method 2: Using Command Line

1. **IMPORTANT**: Right-click on the command prompt or PowerShell and select "Run as administrator"

2. Run the script:
   ```
   python dns_switcher_gui.py
   ```

3. **New**: Use the "Refresh Adapters" button to update the list of network adapters without restarting the program

## Notes

- **This application requires administrator privileges to modify DNS settings**
- The batch files (`run_dns_switcher.bat` and `run_gui_as_admin.bat`) are configured to automatically request administrator privileges when double-clicked
- The application uses `wmic` and `netsh` commands to list adapters and modify DNS settings
- All code is written in English to prevent encoding issues

## Troubleshooting

### "wmic command not found or not available" error

If you encounter this error, it means the Windows Management Instrumentation Command-line (WMIC) tool is not available on your system.

Possible solutions:
1. **Ensure you are running on a Windows operating system** - This application is designed for Windows only
2. **Run as administrator** - Right-click on the batch file or command prompt and select "Run as administrator"
3. **Check command availability**:
   - The application will first try to use WMIC to get network adapters.
   - If WMIC is not available, it will attempt to use PowerShell as a fallback.
4. **Enable WMIC** (if needed):
   - Open Command Prompt as administrator
   - Run `wmic` to see if it's recognized
   - If not, you may need to enable the WMI service
5. **Enable PowerShell** (if needed):
   - PowerShell is typically enabled by default on Windows 7 and later
   - Ensure you have PowerShell version 3.0 or later
6. **Test command availability**: If you encounter issues, open PowerShell as administrator and run `wmic` to check if it's recognized

## License

## Compiled Executables

You can find compiled executables in the `dist` directory:
- `dns_switcher.exe`: Console version
- `dns_switcher_gui.exe`: GUI version

These executables can be run directly without installing Python, but still require administrator privileges.

This project is licensed under the MIT License.