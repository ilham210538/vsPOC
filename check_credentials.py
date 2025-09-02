#!/usr/bin/env python3
"""
Credential and Permission Analysis Script
Helps identify what credentials are being used and what permissions are needed.
"""
import os
import sys
from dotenv import load_dotenv

def main():
    print("=== AZURE AI FOUNDRY CALENDAR AGENT - CREDENTIAL ANALYSIS ===\n")
    
    # Load environment variables
    load_dotenv()
    
    print("📋 CONFIGURATION SUMMARY:")
    print("-" * 50)
    
    # Azure AI Project
    print("🤖 Azure AI Foundry Project:")
    print(f"   - Endpoint: {os.environ.get('PROJECT_ENDPOINT', 'NOT SET')}")
    print(f"   - Model: {os.environ.get('MODEL_DEPLOYMENT_NAME', 'NOT SET')}")
    print()
    
    # Microsoft Graph Configuration
    print("📅 Microsoft Graph Configuration:")
    tenant_id = os.environ.get('GRAPH_TENANT_ID', 'NOT SET')
    client_id = os.environ.get('GRAPH_CLIENT_ID', 'NOT SET')
    target_user = os.environ.get('DEFAULT_USER_UPN', 'NOT SET')
    
    print(f"   - Tenant ID: {tenant_id}")
    print(f"   - Client ID (App Registration): {client_id}")
    print(f"   - Target User Calendar: {target_user}")
    print(f"   - Authentication Method: App-Only (Client Credentials)")
    print()
    
    # Test token acquisition
    print("🔐 CREDENTIAL VALIDATION:")
    print("-" * 50)
    
    try:
        from azure.identity import ClientSecretCredential
        
        if not all([
            os.environ.get('GRAPH_TENANT_ID'),
            os.environ.get('GRAPH_CLIENT_ID'), 
            os.environ.get('GRAPH_CLIENT_SECRET')
        ]):
            print("❌ Missing required environment variables")
            return
            
        cred = ClientSecretCredential(
            tenant_id=os.environ['GRAPH_TENANT_ID'],
            client_id=os.environ['GRAPH_CLIENT_ID'], 
            client_secret=os.environ['GRAPH_CLIENT_SECRET'],
        )
        
        print("   - Attempting to acquire access token...")
        token = cred.get_token('https://graph.microsoft.com/.default')
        print("   ✅ Token acquired successfully!")
        print(f"   - Token type: Bearer")
        print(f"   - Expires at: {token.expires_on}")
        
    except Exception as e:
        print(f"   ❌ Token acquisition failed: {e}")
        print("   💡 This suggests authentication/credential issues")
        
    print()
    
    # Required permissions analysis
    print("🛡️ REQUIRED MICROSOFT GRAPH PERMISSIONS:")
    print("-" * 50)
    print("App Registration needs these APPLICATION permissions:")
    print("   ✅ Calendars.ReadWrite.All")
    print("   ✅ User.Read.All")
    print()
    print("⚠️  IMPORTANT: These must be:")
    print("   1. Added to the App Registration in Azure Portal")
    print("   2. ADMIN CONSENTED by IT Administrator")
    print("   3. Set as APPLICATION permissions (not Delegated)")
    print()
    
    # IT Support Information
    print("📧 FOR IT SUPPORT REQUEST:")
    print("-" * 50)
    print("Please grant the following for our Calendar Agent application:")
    print()
    print(f"Azure AD Tenant: {tenant_id}")
    print(f"App Registration ID: {client_id}")
    print(f"Target User: {target_user}")
    print()
    print("Required Microsoft Graph API Permissions:")
    print("• Calendars.ReadWrite.All (Application)")
    print("• User.Read.All (Application)")
    print()
    print("Actions needed:")
    print("1. Navigate to Azure Portal > App Registrations")
    print(f"2. Find app with ID: {client_id}")
    print("3. Go to API Permissions")
    print("4. Add the above Microsoft Graph permissions")
    print("5. Click 'Grant admin consent' button")
    print("6. Ensure permissions show 'Granted for [organization]' status")
    print()
    
    # Troubleshooting
    print("🔍 TROUBLESHOOTING GUIDE:")
    print("-" * 50)
    print("If still getting 403 errors after permissions are granted:")
    print("1. Wait 5-10 minutes for permission propagation")
    print("2. Verify the app registration client secret hasn't expired")
    print("3. Check that the target user exists in the tenant")
    print("4. Ensure the app is granted permissions in the correct tenant")
    print()

if __name__ == "__main__":
    main()
