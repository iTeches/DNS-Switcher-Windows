"""
DNS Switcher - A Python application to change DNS settings on Windows
"""

import subprocess
import sys
import ctypes
import wmi


def is_admin():
    """Check if the script is running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Relaunch the script with administrator privileges"""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )

def check_command_availability(command, args=None):
    """Check if a command is available"""
    try:
        if args is None:
            args = ["/?"] if command == "wmic" else ["--help"]
        # Check if command is available
        subprocess.run([command] + args, capture_output=True, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def run_command_with_encoding(command, args=None):
    """Run command with proper encoding handling"""
    try:
        result = subprocess.run(
            [command] + (args or []),
            capture_output=True,
            check=True
        )
        # Try to decode with utf-8, fallback to gbk if needed
        try:
            stdout = result.stdout.decode('utf-8')
            stderr = result.stderr.decode('utf-8')
        except UnicodeDecodeError:
            stdout = result.stdout.decode('gbk', errors='replace')
            stderr = result.stderr.decode('gbk', errors='replace')
        return stdout, stderr
    except subprocess.CalledProcessError as e:
        # Handle error output encoding
        try:
            stderr = e.stderr.decode('utf-8')
        except UnicodeDecodeError:
            stderr = e.stderr.decode('gbk', errors='replace')
        raise subprocess.CalledProcessError(e.returncode, e.cmd, e.output, stderr)

def get_network_adapters():
    """Get a list of network adapters with their NetConnectionID (used by netsh)."""
    try:
        # Use WMI to get network adapters with their NetConnectionID
        c = wmi.WMI()
        adapters = []

        # Check if WMI query returns valid results
        network_adapters = c.Win32_NetworkAdapter()
        if network_adapters is None:
            print("WMI query returned None for network adapters.")
            return []

        for nic in network_adapters:
            # Ensure nic is not None and has required attributes
            if nic is not None and hasattr(nic, 'NetEnabled') and hasattr(nic, 'NetConnectionID'):
                if nic.NetEnabled and nic.NetConnectionID:
                    # Get additional details using netsh
                    try:
                        # Get adapter type using netsh
                        type_stdout, _ = run_command_with_encoding(
                            "netsh", ["interface", "show", "interface", nic.NetConnectionID]
                        )
                        adapter_type = "Unknown"
                        for line in type_stdout.split('\n'):
                            if "Type" in line:
                                adapter_type = line.split(':')[-1].strip()
                                break
                    except subprocess.CalledProcessError:
                        adapter_type = "Unknown"

                    # Ensure nic has required attributes before accessing
                    if hasattr(nic, 'Name') and hasattr(nic, 'InterfaceIndex'):
                        adapters.append({
                            "name": nic.NetConnectionID,  # This is the name used by netsh
                            "description": nic.Name,       # This is the friendly name
                            "index": nic.InterfaceIndex,
                            "type": adapter_type
                        })
                    else:
                        # Skip adapter if it doesn't have required attributes
                        continue

        if adapters:
            return adapters
        else:
            print("No active network adapters found via WMI.")
    except Exception as e:
        print(f"Error getting network adapters via WMI: {str(e)}")

    # Fall back to netsh if WMI fails
    if check_command_availability("netsh"):
        try:
            # Get network adapters using netsh
            result_stdout, _ = run_command_with_encoding(
                "netsh", ["interface", "show", "interface"]
            )

            # Parse the output
            lines = result_stdout.strip().split('\n')
            adapters = []

            # Skip the header lines
            for line in lines[3:]:
                if line.strip():
                    # Split by whitespace and handle multiple spaces
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        # Extract information
                        admin_state = parts[0]
                        state = parts[1]
                        type = parts[2]
                        # The name is everything else
                        name = ' '.join(parts[3:])

                        # Only include adapters that are enabled
                        if admin_state.lower() == "enabled" and state.lower() == "connected":
                            # Get interface index using netsh
                            try:
                                index_stdout, _ = run_command_with_encoding(
                                    "netsh", ["interface", "ipv4", "show", "interfaces", "interface=", name]
                                )
                                index = "unknown"
                                for idx_line in index_stdout.split('\n'):
                                    if "Idx" in idx_line:
                                        index = idx_line.split(':')[-1].strip()
                                        break
                            except subprocess.CalledProcessError:
                                index = "unknown"

                            adapters.append({
                                "name": name,
                                "description": name,
                                "index": index,
                                "type": type
                            })

            return adapters
        except subprocess.CalledProcessError as e:
            print(f"Error getting network adapters with netsh: {e}")
            return []

    # If all methods fail
    print("Error: Could not retrieve network adapters.")
    print("None of the following commands are available or functioning correctly: wmic, PowerShell, netsh.")
    print("Possible solutions:")
    print("1. Ensure you are running on a Windows operating system.")
    print("2. Check if these commands are enabled on your system.")
    print("3. Run the application as administrator.")
    return []


def get_current_dns(adapter_name):
    """Get current DNS settings for the specified adapter"""
    try:
        # Get current DNS settings using netsh
        stdout, _ = run_command_with_encoding(
            "netsh", ["interface", "ip", "show", "dns", f"name={adapter_name}"]
        )
        return stdout
    except subprocess.CalledProcessError as e:
        return f"Error getting DNS settings: {e.stderr}"


def display_adapters(adapters):
    """Display the list of network adapters"""
    print("\nAvailable Network Adapters:")
    print("=" * 50)
    for i, adapter in enumerate(adapters):
        print(f"{i + 1}. {adapter['name']} (Type: {adapter['type']})")


def select_adapter(adapters):
    """Let user select a network adapter"""
    if not adapters:
        print("No network adapters found.")
        return None
    
    while True:
        try:
            choice = int(input("\nSelect an adapter (enter number): ")) - 1
            if 0 <= choice < len(adapters):
                return adapters[choice]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")


def set_dns(adapter_name, dns_servers):
    """Set DNS servers for the specified adapter"""
    try:
        # Set primary DNS
        command = [
            "netsh", "interface", "ip", "set", "dns", 
            f"name={adapter_name}", "source=static", f"addr={dns_servers[0]}"
        ]
        subprocess.run(command, check=True)
        
        # Add secondary DNS if provided
        if len(dns_servers) > 1:
            command = [
                "netsh", "interface", "ip", "add", "dns", 
                f"name={adapter_name}", f"addr={dns_servers[1]}", "index=2"
            ]
            subprocess.run(command, check=True)
        
        print(f"DNS settings updated successfully for {adapter_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error setting DNS: {e}")
        return False


def reset_dns(adapter_name):
    """Reset DNS to obtain automatically"""
    try:
        command = [
            "netsh", "interface", "ip", "set", "dns", 
            f"name={adapter_name}", "source=dhcp"
        ]
        subprocess.run(command, check=True)
        print(f"DNS settings reset to automatic for {adapter_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error resetting DNS: {e}")
        return False


def main():
    """Main function"""
    print("DNS Switcher - Windows DNS Configuration Tool")
    print("=" * 50)
    
    # Check if running as administrator
    if not is_admin():
        print("This script requires administrator privileges to modify DNS settings.")
        try:
            choice = input("\nWould you like to restart the script with administrator privileges? (y/n): ").strip().lower()
            if choice == 'y' or choice == 'yes':
                run_as_admin()
                sys.exit(0)
            else:
                print("Exiting without administrator privileges.")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            sys.exit(1)
    
    # Get network adapters
    adapters = get_network_adapters()
    
    if not adapters:
        print("No network adapters found. Exiting.")
        sys.exit(1)
    
    # Display adapters and let user select one
    display_adapters(adapters)
    selected_adapter = select_adapter(adapters)
    
    if not selected_adapter:
        print("No adapter selected. Exiting.")
        sys.exit(1)
    
    # Display current DNS settings for selected adapter
    print(f"\nCurrent DNS settings for {selected_adapter['name']}:")
    print("-" * 50)
    current_dns = get_current_dns(selected_adapter["name"])
    print(current_dns)
    
    # Menu for DNS options
    while True:
        print("\nDNS Options:")
        print("1. Set Google DNS (8.8.8.8, 8.8.4.4)")
        print("2. Set Cloudflare DNS (1.1.1.1, 1.0.0.1)")
        print("3. Set OpenDNS (208.67.222.222, 208.67.220.220)")
        print("4. Set AliDNS (223.5.5.5, 223.6.6.6)")
        print("5. Set 114DNS (114.114.114.114, 114.114.115.115)")
        print("6. Custom DNS")
        print("7. Reset to automatic DNS")
        print("8. Re-select network adapter")
        print("9. Exit")
        
        choice = input("\nSelect an option (1-9): ").strip()
        
        if choice == "1":
            set_dns(selected_adapter["name"], ["8.8.8.8", "8.8.4.4"])
        elif choice == "2":
            set_dns(selected_adapter["name"], ["1.1.1.1", "1.0.0.1"])
        elif choice == "3":
            set_dns(selected_adapter["name"], ["208.67.222.222", "208.67.220.220"])
        elif choice == "4":
            set_dns(selected_adapter["name"], ["223.5.5.5", "223.6.6.6"])
        elif choice == "5":
            set_dns(selected_adapter["name"], ["114.114.114.114", "114.114.115.115"])
        elif choice == "6":
            primary = input("Enter primary DNS server: ").strip()
            secondary = input("Enter secondary DNS server (optional, press Enter to skip): ").strip()
            dns_servers = [primary]
            if secondary:
                dns_servers.append(secondary)
            set_dns(selected_adapter["name"], dns_servers)
        elif choice == "7":
            reset_dns(selected_adapter["name"])
        elif choice == "8":
            print("\nRefreshing network adapters...")
            adapters = get_network_adapters()
            if not adapters:
                print("No network adapters found. Exiting.")
                sys.exit(1)
            display_adapters(adapters)
            selected_adapter = select_adapter(adapters)
            if not selected_adapter:
                print("No adapter selected. Exiting.")
                sys.exit(1)
            print(f"\nCurrent DNS settings for {selected_adapter['name']}:")
            print("-" * 50)
            current_dns = get_current_dns(selected_adapter["name"])
            print(current_dns)
        elif choice == "9":
            print("Exiting DNS Switcher. Goodbye!")
            break
        else:
            print("Invalid option. Please select a number between 1 and 8.")


if __name__ == "__main__":
    main()