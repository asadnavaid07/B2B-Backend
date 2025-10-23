"""
Test script to verify SMTP configuration
This script checks if SMTP credentials are properly configured
"""
import os
from dotenv import load_dotenv

def check_smtp_config():
    """Check if SMTP configuration is properly set up"""
    load_dotenv()
    
    print("SMTP Configuration Check")
    print("=" * 30)
    
    # Check required environment variables
    required_vars = {
        'SMTP_SERVER': os.getenv('SMTP_SERVER'),
        'SMTP_PORT': os.getenv('SMTP_PORT'),
        'SMTP_USERNAME': os.getenv('SMTP_USERNAME'),
        'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD'),
        'EMAIL_FROM': os.getenv('EMAIL_FROM')
    }
    
    all_configured = True
    
    for var_name, var_value in required_vars.items():
        if var_value:
            print(f"[OK] {var_name}: {var_value}")
        else:
            print(f"[MISSING] {var_name}: Not configured")
            all_configured = False
    
    print("\n" + "=" * 30)
    
    if all_configured:
        print("[SUCCESS] All SMTP configuration variables are set!")
        print("You can now run: python app/test.py")
    else:
        print("[ERROR] Some SMTP configuration variables are missing.")
        print("Please add the missing variables to your .env file:")
        print("\nExample .env configuration:")
        print("SMTP_SERVER=smtp.gmail.com")
        print("SMTP_PORT=587")
        print("SMTP_USERNAME=your-email@gmail.com")
        print("SMTP_PASSWORD=your-app-password")
        print("EMAIL_FROM=your-email@gmail.com")
    
    return all_configured

if __name__ == "__main__":
    check_smtp_config()
