import streamlit as st
import requests

# streamlit run app.py --server.sslCertFile=cert.pem --server.sslKeyFile=key.pem

APP_ID = st.secrets["facebook"]["app_id"]
APP_SECRET = st.secrets["facebook"]["app_secret"]
REDIRECT_URI = 'https://autoposter.streamlit.app/'
# SSL_CERT_PATH = 'cert.pem'
# SSL_KEY_PATH = 'key.pem'

def login():
    permissions = "pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish"
    auth_url = f"https://www.facebook.com/v20.0/dialog/oauth?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&scope={permissions}"
    st.markdown(f"[Login with Facebook]({auth_url})")

def get_access_token(code):
    token_url = f"https://graph.facebook.com/v20.0/oauth/access_token?client_id={APP_ID}&redirect_uri={REDIRECT_URI}&client_secret={APP_SECRET}&code={code}"
    response = requests.get(token_url)
    return response.json().get('access_token')

def get_user_pages(access_token):
    pages_url = f"https://graph.facebook.com/v20.0/me/accounts?access_token={access_token}"
    pages_response = requests.get(pages_url)
    return pages_response.json().get('data', [])

def get_instagram_account(page_id, page_token):
    ig_account_url = f"https://graph.facebook.com/v20.0/{page_id}?fields=instagram_business_account&access_token={page_token}"
    ig_response = requests.get(ig_account_url)
    ig_data = ig_response.json()
    return ig_data.get('instagram_business_account', {}).get('id')

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
        st.write(f"Page ID: {st.session_state.page_id}")
        st.write(f"Instagram User ID: {st.session_state.ig_user_id}")

        image_url = st.text_input("Image URL")
        message = st.text_input("Message for Facebook")
        caption = st.text_input("Caption for Instagram")

        if st.button("Post Image"):
            if image_url and message and caption:
                fb_result = post_to_facebook(st.session_state.page_id, st.session_state.page_token, image_url, message)
                ig_result = post_to_instagram(st.session_state.ig_user_id, st.session_state.page_token, image_url, caption)
                st.write("Facebook result:", fb_result)
                st.write("Instagram result:", ig_result)
            else:
                st.warning("Please fill in all fields")
    else:
        login()
        code = st.query_params.get("code")
        if code:
            access_token = get_access_token(code)
            if access_token:
                st.session_state.access_token = access_token
                pages = get_user_pages(access_token)
                if pages:
                    st.session_state.page_token = pages[0]['access_token']
                    st.session_state.page_id = pages[0]['id']
                    st.session_state.ig_user_id = get_instagram_account(pages[0]['id'], pages[0]['access_token'])
                    st.rerun()
                else:
                    st.error("No pages found. Make sure you have a Facebook Page.")
            else:
                st.error("Failed to get access token.")

if __name__ == "__main__":
  main()