"""
DNS Switcher GUI - A graphical interface for changing DNS settings on Windows
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import ctypes
import sys
import wmi


class DNSSwitcherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DNS Switcher for Windows")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Check if running as administrator
        if not self.is_admin():
            result = messagebox.askyesno("Permission Required", 
                "This application requires administrator privileges to modify DNS settings.\n"
                "Would you like to restart the application with administrator privileges?")
            if result:
                self.run_as_admin()
                sys.exit(0)
            else:
                sys.exit(1)
        
        # Predefined DNS servers
        self.dns_options = {
            "Google DNS": ["8.8.8.8", "8.8.4.4"],
            "Cloudflare DNS": ["1.1.1.1", "1.0.0.1"],
            "OpenDNS": ["208.67.222.222", "208.67.220.220"],
            "AliDNS": ["223.5.5.5", "223.6.6.6"],
            "114DNS": ["114.114.114.114", "114.114.115.115"]
        }
        
        # Get network adapters
        self.adapters = self.get_network_adapters()
        
        # Create GUI elements
        self.create_widgets()
        
        # Populate adapter dropdown
        self.populate_adapter_dropdown()
    
    def is_admin(self):
        """Check if the script is running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def run_as_admin(self):
        """Relaunch the script with administrator privileges"""
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
    
    def check_command_availability(self, command, args=None):
        """Check if a command is available"""
        try:
            if args is None:
                args = ["/?"] if command == "wmic" else ["--help"]
            # Check if command is available
            subprocess.run([command] + args, capture_output=True, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def run_command_with_encoding(self, command, args=None):
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

    def get_network_adapters(self):
        """Get a list of network adapters with their NetConnectionID (used by netsh)."""
        try:
            # Use WMI to get network adapters with their NetConnectionID
            c = wmi.WMI()
            adapters = []

            # Check if WMI query returns valid results
            network_adapters = c.Win32_NetworkAdapter()
            if network_adapters is None:
                messagebox.showerror("Error", "WMI query returned None for network adapters.")
                return []

            for nic in network_adapters:
                # Ensure nic is not None and has required attributes
                if nic is not None and hasattr(nic, 'NetEnabled') and hasattr(nic, 'NetConnectionID'):
                    if nic.NetEnabled and nic.NetConnectionID:
                        # Get adapter type using netsh
                        try:
                            type_stdout, _ = self.run_command_with_encoding(
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
                messagebox.showerror("Error", "No active network adapters found via WMI.")
        except Exception as e:
            messagebox.showerror("Error", f"Error getting network adapters via WMI: {str(e)}")

        # Fall back to netsh if WMI fails
        if self.check_command_availability("netsh"):
            try:
                # Get network adapters using netsh
                result_stdout, _ = self.run_command_with_encoding(
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
                                    index_stdout, _ = self.run_command_with_encoding(
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
                messagebox.showerror("Error", f"Error getting network adapters with netsh: {e}")
                return []

        # If all methods fail
        messagebox.showerror("Error", 
            "Could not retrieve network adapters.\n"+
            "None of the following methods are available or functioning correctly: WMI, netsh.\n\n"+
            "Possible solutions:\n"+
            "1. Ensure you are running on a Windows operating system.\n"+
            "2. Check if WMI service is running on your system.\n"+
            "3. Run the application as administrator.")
        return []
    
    def get_current_dns(self, adapter_name):
        """Get current DNS settings for the specified adapter"""
        try:
            # Get current DNS settings using netsh
            stdout, _ = self.run_command_with_encoding(
                "netsh", ["interface", "ip", "show", "dns", f"name={adapter_name}"]
            )
            return stdout
        except subprocess.CalledProcessError as e:
            return f"Error getting DNS settings: {e.stderr}"
    
    def populate_adapter_dropdown(self):
        """Populate the adapter dropdown with available adapters"""
        adapter_names = [adapter["name"] for adapter in self.adapters]
        self.adapter_combobox['values'] = adapter_names
        
        if adapter_names:
            current_value = self.adapter_combobox.get()
            if current_value in adapter_names:
                self.adapter_combobox.set(current_value)
            else:
                self.adapter_combobox.set(adapter_names[0])
            self.update_current_dns_display()
        else:
            self.adapter_combobox.set('')
            self.current_dns_text.delete(1.0, tk.END)
            self.current_dns_text.insert(tk.END, "No network adapters found.")
    
    def refresh_adapters(self):
        """Refresh the list of network adapters"""
        self.adapters = self.get_network_adapters()
        self.populate_adapter_dropdown()
        messagebox.showinfo("Success", "Network adapters refreshed successfully.")
    
    def update_current_dns_display(self):
        """Update the current DNS display when a new adapter is selected"""
        selected_adapter = self.adapter_combobox.get()
        if selected_adapter:
            current_dns = self.get_current_dns(selected_adapter)
            self.current_dns_text.delete(1.0, tk.END)
            self.current_dns_text.insert(tk.END, current_dns)
    
    def set_dns(self, adapter_name, dns_servers):
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
            
            messagebox.showinfo("Success", f"DNS settings updated successfully for {adapter_name}")
            self.update_current_dns_display()
            return True
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error setting DNS: {e}")
            return False
    
    def reset_dns(self, adapter_name):
        """Reset DNS to obtain automatically"""
        try:
            command = [
                "netsh", "interface", "ip", "set", "dns", 
                f"name={adapter_name}", "source=dhcp"
            ]
            subprocess.run(command, check=True)
            messagebox.showinfo("Success", f"DNS settings reset to automatic for {adapter_name}")
            self.update_current_dns_display()
            return True
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Error resetting DNS: {e}")
            return False
    
    def apply_predefined_dns(self):
        """Apply selected predefined DNS settings"""
        selected_adapter = self.adapter_combobox.get()
        selected_dns = self.dns_combobox.get()
        
        if not selected_adapter:
            messagebox.showerror("Error", "Please select a network adapter.")
            return
        
        if not selected_dns:
            messagebox.showerror("Error", "Please select a DNS option.")
            return
        
        if selected_dns in self.dns_options:
            self.set_dns(selected_adapter, self.dns_options[selected_dns])
    
    def apply_custom_dns(self):
        """Apply custom DNS settings"""
        selected_adapter = self.adapter_combobox.get()
        primary_dns = self.primary_dns_entry.get().strip()
        secondary_dns = self.secondary_dns_entry.get().strip()
        
        if not selected_adapter:
            messagebox.showerror("Error", "Please select a network adapter.")
            return
        
        if not primary_dns:
            messagebox.showerror("Error", "Please enter a primary DNS server.")
            return
        
        dns_servers = [primary_dns]
        if secondary_dns:
            dns_servers.append(secondary_dns)
        
        self.set_dns(selected_adapter, dns_servers)
    
    def reset_to_automatic(self):
        """Reset DNS settings to automatic"""
        selected_adapter = self.adapter_combobox.get()
        
        if not selected_adapter:
            messagebox.showerror("Error", "Please select a network adapter.")
            return
        
        self.reset_dns(selected_adapter)
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Adapter selection with refresh button
        ttk.Label(main_frame, text="Select Network Adapter:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        adapter_frame = ttk.Frame(main_frame)
        adapter_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        self.adapter_combobox = ttk.Combobox(adapter_frame, width=40, state="readonly")
        self.adapter_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.adapter_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_current_dns_display())

        refresh_button = ttk.Button(adapter_frame, text=" Refresh ", command=self.refresh_adapters)
        refresh_button.pack(side=tk.RIGHT)
        
        # Current DNS settings
        ttk.Label(main_frame, text="Current DNS Settings:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.current_dns_text = tk.Text(main_frame, height=4, width=60)
        self.current_dns_text.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        
        # Predefined DNS options
        ttk.Label(main_frame, text="Predefined DNS Options:").grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        self.dns_combobox = ttk.Combobox(main_frame, width=30, state="readonly", 
                                        values=list(self.dns_options.keys()))
        self.dns_combobox.grid(row=5, column=0, sticky=tk.W, pady=(0, 10))
        
        ttk.Button(main_frame, text="Apply Predefined DNS", 
                  command=self.apply_predefined_dns).grid(row=5, column=1, sticky=tk.W, pady=(0, 10))
        
        # Custom DNS options
        ttk.Label(main_frame, text="Custom DNS Settings:").grid(row=6, column=0, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(main_frame, text="Primary DNS:").grid(row=7, column=0, sticky=tk.W)
        self.primary_dns_entry = ttk.Entry(main_frame, width=30)
        self.primary_dns_entry.grid(row=7, column=1, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(main_frame, text="Secondary DNS (optional):").grid(row=8, column=0, sticky=tk.W)
        self.secondary_dns_entry = ttk.Entry(main_frame, width=30)
        self.secondary_dns_entry.grid(row=8, column=1, sticky=tk.W, pady=(0, 10))
        
        ttk.Button(main_frame, text="Apply Custom DNS", 
                  command=self.apply_custom_dns).grid(row=9, column=0, sticky=tk.W, pady=(0, 10))
        
        # Reset button
        ttk.Button(main_frame, text="Reset to Automatic DNS", 
                  command=self.reset_to_automatic).style = "Accent.TButton"
        reset_button = ttk.Button(main_frame, text="Reset to Automatic DNS", 
                                 command=self.reset_to_automatic)
        reset_button.grid(row=9, column=1, sticky=tk.W, pady=(0, 10))
        
        # Exit button
        ttk.Button(main_frame, text="Exit", command=self.root.quit).grid(row=10, column=1, sticky=tk.E, pady=(10, 0))


def main():
    root = tk.Tk()
    app = DNSSwitcherGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()