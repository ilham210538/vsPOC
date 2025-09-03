"""
Debug script to check Azure AD app permissions and token claims
"""

import os
import json
import base64
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential

# Load environment
load_dotenv()

def decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload (claims)"""
    try:
        # Split the token into parts
        header_b64, payload_b64, signature_b64 = token.split(".")
        
        # Add padding if needed
        payload_b64 += '=' * (-len(payload_b64) % 4)
        
        # Decode the payload
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        return payload
    except Exception as e:
        print(f"Error decoding JWT: {e}")
        return {}

def main():
    print("=== Azure AD App Permissions Debug ===\n")
    
    # Check environment variables
    tenant_id = os.getenv("GRAPH_TENANT_ID")
    client_id = os.getenv("GRAPH_CLIENT_ID")
    client_secret = os.getenv("GRAPH_CLIENT_SECRET")
    
    print(f"Tenant ID: {tenant_id}")
    print(f"Client ID: {client_id}")
    print(f"Client Secret: {'*' * 20 if client_secret else 'NOT SET'}")
    print()
    
    if not all([tenant_id, client_id, client_secret]):
        print("❌ Missing required environment variables!")
        return
    
    try:
        # Create credential
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        # Request token
        print("🔑 Requesting access token...")
        scope = "https://graph.microsoft.com/.default"
        token_response = credential.get_token(scope)
        
        print(f"✅ Token acquired successfully")
        print(f"Token expires at: {token_response.expires_on}")
        print()
        
        # Decode token
        payload = decode_jwt_payload(token_response.token)
        
        if payload:
            print("=== Token Claims ===")
            for key, value in sorted(payload.items()):
                if key == 'roles':
                    print(f"{key:15}: {value}")
                    if isinstance(value, list) and value:
                        for role in value:
                            print(f"                 - {role}")
                    elif not value:
                        print(f"                 (empty list)")
                elif key in ['aud', 'iss', 'tid', 'appid', 'sub', 'iat', 'exp', 'nbf']:
                    if key in ['iat', 'exp', 'nbf']:
                        import datetime
                        dt = datetime.datetime.fromtimestamp(value, tz=datetime.timezone.utc)
                        print(f"{key:15}: {value} ({dt})")
                    else:
                        print(f"{key:15}: {value}")
            print()
            
            # Check required roles
            required_roles = ["Calendars.ReadWrite", "User.Read.All"]
            token_roles = payload.get('roles', [])
            
            print("=== Permission Check ===")
            for role in required_roles:
                if role in token_roles:
                    print(f"✅ {role}")
                else:
                    print(f"❌ {role} - MISSING")
            
            if not token_roles:
                print("\n⚠️  NO ROLES FOUND IN TOKEN!")
                print("This usually means:")
                print("1. Application permissions haven't been granted admin consent")
                print("2. The app registration doesn't have the required API permissions")
                print("3. There's a delay in permission propagation")
                print("4. Token was cached before permissions were granted")
                print("\n🔧 NEXT STEPS:")
                print("1. Ask IT to click 'Grant admin consent' button in Azure portal")
                print("2. Wait 5-10 minutes for Azure AD to propagate changes")
                print("3. Clear any token caches and retry")
                print(f"4. Verify permissions at: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/{client_id}")
                print("\n📋 Required Application Permissions:")
                print("   • Microsoft Graph > Calendars.ReadWrite (Application)")
                print("   • Microsoft Graph > User.Read.All (Application)")
                print("   • Microsoft Graph > MailboxSettings.Read (Application)")
                print("\n⚠️  Make sure these are APPLICATION permissions, not DELEGATED!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
