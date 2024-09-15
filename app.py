import streamlit as st
import requests

# streamlit run app.py --server.sslCertFile=cert.pem --server.sslKeyFile=key.pem

APP_ID = st.secrets["facebook"]["app_id"]
APP_SECRET = st.secrets["facebook"]["app_secret"]
REDIRECT_URI = 'https://autoposter.streamlit.app/'
# SSL_CERT_PATH = 'cert.pem'
# SSL_KEY_PATH = 'key.pem'


st.set_page_config(
    page_title="Social Media Image Poster",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded",
)

def facebook_login():
    permissions = "pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish"
    auth_url = f"https://www.facebook.com/v20.0/dialog/oauth?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&scope={permissions}"
    st.markdown(f"[Login with Facebook]({auth_url})")

def instagram_login():
    permissions = "instagram_basic,instagram_content_publish"
    auth_url = f"https://www.facebook.com/v20.0/dialog/oauth?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&scope={permissions}"
    st.markdown(f"[Login with Instagram]({auth_url})")

def get_access_token(code):
    token_url = f"https://graph.facebook.com/v20.0/oauth/access_token?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&client_secret={APP_SECRET}&code={code}"
    response = requests.get(token_url)
    return response.json().get('access_token')

def get_user_pages(access_token):
    pages_url = f"https://graph.facebook.com/v20.0/me/accounts?access_token={access_token}"
    pages_response = requests.get(pages_url)
    return pages_response.json().get('data', [])

def get_instagram_accounts(access_token):
    ig_accounts_url = f"https://graph.facebook.com/v20.0/me/accounts?fields=instagram_business_account{{id,name,username}}&access_token={access_token}"
    ig_response = requests.get(ig_accounts_url)
    ig_data = ig_response.json().get('data', [])
    accounts = []
    for account in ig_data:
        if 'instagram_business_account' in account:
            ig_account = account['instagram_business_account']
            accounts.append({
                'id': ig_account['id'],
                'name': ig_account.get('name', 'Unknown'),
                'username': ig_account.get('username', 'Unknown')
            })
    return accounts

def post_to_facebook(page_id, page_token, image_url, message):
    post_url = f'https://graph.facebook.com/v20.0/{page_id}/photos'
    data = {
        'url': image_url,
        'message': message,
        'access_token': page_token
    }
    response = requests.post(post_url, data=data)
    return response.json()

def post_to_instagram(ig_user_id, access_token, image_url, caption):
    media_url = f'https://graph.facebook.com/v20.0/{ig_user_id}/media'
    media_params = {
        'image_url': image_url,
        'caption': caption,
        'access_token': access_token
    }
    response = requests.post(media_url, params=media_params)
    result = response.json()
    
    if 'id' in result:
        creation_id = result['id']
        publish_url = f'https://graph.facebook.com/v20.0/{ig_user_id}/media_publish'
        publish_params = {
            'creation_id': creation_id,
            'access_token': access_token
        }
        publish_response = requests.post(publish_url, params=publish_params)
        return publish_response.json()
    return result

def main():
    st.title("Social Media Image Poster")

    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
        st.session_state.page_token = None
        st.session_state.page_id = None
        st.session_state.ig_user_id = None

    if st.session_state.access_token:
        st.success("You are logged in!")
        st.write(f"Access token: {st.session_state.access_token[:10]}...")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Facebook Posting")
            pages = get_user_pages(st.session_state.access_token)
            if pages:
                selected_page = st.selectbox("Select Facebook Page", [f"{page['name']} ({page['id']})" for page in pages])
                selected_page_id = selected_page.split('(')[-1].strip(')')
                st.session_state.page_id = selected_page_id
                st.session_state.page_token = next(page['access_token'] for page in pages if page['id'] == selected_page_id)
                
                image_url = st.text_input("Image URL for Facebook")
                message = st.text_input("Message for Facebook")
                
                if st.button("Post to Facebook"):
                    if image_url and message:
                        result = post_to_facebook(st.session_state.page_id, st.session_state.page_token, image_url, message)
                        st.write("Facebook result:", result)
                    else:
                        st.warning("Please fill in all Facebook fields")
            else:
                st.warning("No Facebook Pages found. Make sure you have a Facebook Page associated with your account.")
        
        with col2:
            st.subheader("Instagram Posting")
            ig_accounts = get_instagram_accounts(st.session_state.access_token)
            if ig_accounts:
                selected_account = st.selectbox("Select Instagram Account", [f"{account['name']} (@{account['username']})" for account in ig_accounts])
                selected_account_id = next(account['id'] for account in ig_accounts if f"{account['name']} (@{account['username']})" == selected_account)
                st.session_state.ig_user_id = selected_account_id
                
                ig_image_url = st.text_input("Image URL for Instagram")
                ig_caption = st.text_input("Caption for Instagram")
                
                if st.button("Post to Instagram"):
                    if ig_image_url and ig_caption:
                        result = post_to_instagram(st.session_state.ig_user_id, st.session_state.access_token, ig_image_url, ig_caption)
                        st.write("Instagram result:", result)
                    else:
                        st.warning("Please fill in all Instagram fields")
            else:
                st.warning("No Instagram Business accounts found. Make sure you have connected an Instagram Business account to your Facebook account.")
    else:
        st.write("Please log in to post to Facebook or Instagram.")
        col1, col2 = st.columns(2)
        with col1:
            facebook_login()
        with col2:
            instagram_login()
        
        code = st.query_params.get("code")
        if code:
            access_token = get_access_token(code)
            if access_token:
                st.session_state.access_token = access_token
                st.rerun()
            else:
                st.error("Failed to get access token.")

if __name__ == "__main__":
    main()