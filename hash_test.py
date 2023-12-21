import streamlit_authenticator as stauth

hashed_password = stauth.Hasher(['password']).generate()
print(hashed_password)

