#!/usr/bin/env python3
"""
Multi-User Management Script
Helps configure and run the multi-user dashboard watcher
"""

import json
import os
import sys
import asyncio
from multi_user_watcher import MultiUserWatcher

def load_config():
    """Load the user configuration"""
    try:
        with open("app/config/users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ app/config/users.json not found!")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in app/config/users.json: {e}")
        return None

def save_config(config):
    """Save the user configuration"""
    try:
        with open("app/config/users.json", "w") as f:
            json.dump(config, f, indent=2)
        print("✅ Configuration saved successfully!")
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")

def show_users(config):
    """Display all users and their status"""
    print("\n👥 Current Users:")
    print("=" * 60)
    for i, user in enumerate(config['users'], 1):
        status = "✅ ENABLED" if user.get('enabled', True) else "❌ DISABLED"
        print(f"{i}. {user['name']} ({user['username']}) - {status}")
        print(f"   ID: {user['id']}")
        print(f"   Interval: {user.get('capture_interval', 20)}s")
        print(f"   Max Captures: {user.get('max_captures', 2000)}")
        print()

def edit_user(config):
    """Edit a specific user"""
    show_users(config)
    
    try:
        choice = int(input("Enter user number to edit (0 to cancel): "))
        if choice == 0:
            return
        if 1 <= choice <= len(config['users']):
            user = config['users'][choice - 1]
            print(f"\n📝 Editing user: {user['name']}")
            
            # Edit user details
            user['name'] = input(f"Name [{user['name']}]: ") or user['name']
            user['username'] = input(f"Username [{user['username']}]: ") or user['username']
            user['password'] = input(f"Password [{'*' * len(user['password'])}]: ") or user['password']
            
            # Edit settings
            try:
                interval = input(f"Capture interval (seconds) [{user.get('capture_interval', 20)}]: ")
                if interval:
                    user['capture_interval'] = int(interval)
            except ValueError:
                print("⚠️ Invalid interval, keeping current value")
            
            try:
                max_captures = input(f"Max captures [{user.get('max_captures', 2000)}]: ")
                if max_captures:
                    user['max_captures'] = int(max_captures)
            except ValueError:
                print("⚠️ Invalid max captures, keeping current value")
            
            enabled = input(f"Enabled (y/n) [{'y' if user.get('enabled', True) else 'n'}]: ").lower()
            user['enabled'] = enabled in ['y', 'yes', '1', 'true']
            
            save_config(config)
            print(f"✅ User {user['name']} updated successfully!")
        else:
            print("❌ Invalid user number!")
    except ValueError:
        print("❌ Invalid input!")

def add_user(config):
    """Add a new user"""
    print("\n➕ Adding new user...")
    
    user_id = input("User ID (e.g., user4): ")
    if not user_id:
        print("❌ User ID is required!")
        return
    
    # Check if user ID already exists
    if any(user['id'] == user_id for user in config['users']):
        print("❌ User ID already exists!")
        return
    
    name = input("Name: ")
    username = input("Username/Email: ")
    password = input("Password: ")
    
    try:
        interval = int(input("Capture interval (seconds) [20]: ") or "20")
        max_captures = int(input("Max captures [2000]: ") or "2000")
    except ValueError:
        print("⚠️ Using default values for interval and max captures")
        interval = 20
        max_captures = 2000
    
    new_user = {
        "id": user_id,
        "name": name,
        "username": username,
        "password": password,
        "enabled": True,
        "capture_interval": interval,
        "max_captures": max_captures
    }
    
    config['users'].append(new_user)
    save_config(config)
    print(f"✅ User {name} added successfully!")

def remove_user(config):
    """Remove a user"""
    show_users(config)
    
    try:
        choice = int(input("Enter user number to remove (0 to cancel): "))
        if choice == 0:
            return
        if 1 <= choice <= len(config['users']):
            user = config['users'][choice - 1]
            confirm = input(f"Are you sure you want to remove {user['name']}? (y/n): ").lower()
            if confirm in ['y', 'yes']:
                removed_user = config['users'].pop(choice - 1)
                save_config(config)
                print(f"✅ User {removed_user['name']} removed successfully!")
            else:
                print("❌ User removal cancelled.")
        else:
            print("❌ Invalid user number!")
    except ValueError:
        print("❌ Invalid input!")

def test_websocket():
    """Test WebSocket connection"""
    print("\n🔧 Testing WebSocket connection...")
    try:
        from ..websocket.quick_checker import quick_check
        import asyncio
        
        config = load_config()
        if config:
            endpoint = config['websocket']['endpoint']
            success = asyncio.run(quick_check(endpoint))
            if success:
                print("✅ WebSocket connection successful!")
            else:
                print("❌ WebSocket connection failed!")
                print("💡 Make sure the server is running: python ws_server.py")
    except Exception as e:
        print(f"❌ Error testing WebSocket: {e}")

def run_watcher():
    """Run the multi-user watcher"""
    print("\n🚀 Starting multi-user watcher...")
    try:
        asyncio.run(MultiUserWatcher().run_all_users())
    except KeyboardInterrupt:
        print("\n🛑 Watcher stopped by user")
    except Exception as e:
        print(f"❌ Error running watcher: {e}")

def main():
    """Main menu"""
    while True:
        print("\n" + "=" * 50)
        print("🎯 Multi-User Dashboard Watcher Management")
        print("=" * 50)
        print("1. Show all users")
        print("2. Edit user")
        print("3. Add user")
        print("4. Remove user")
        print("5. Test WebSocket connection")
        print("6. Run multi-user watcher")
        print("7. Exit")
        print("-" * 50)
        
        try:
            choice = input("Enter your choice (1-7): ")
            
            config = load_config()
            if not config:
                print("❌ Cannot load configuration!")
                return
            
            if choice == "1":
                show_users(config)
            elif choice == "2":
                edit_user(config)
            elif choice == "3":
                add_user(config)
            elif choice == "4":
                remove_user(config)
            elif choice == "5":
                test_websocket()
            elif choice == "6":
                run_watcher()
            elif choice == "7":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice!")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 