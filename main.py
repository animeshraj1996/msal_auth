"""FastAPI MSAL Implementation"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import msal
import requests as rq
from urllib.parse import urlparse, parse_qs


app = FastAPI()
templates = Jinja2Templates(directory="templates")

###############################################################################
############################# Azure App Credentials ###########################
###############################################################################

CLIENT_ID = "b8aca2aa-b0b6-4372-9744-c95cfb5f0f98"
CLIENT_SECRET = "e2Z8Q~JV-ZM4UrlRHLoSJiS9phqUQomfYkqbMbDG"
AUTHORITY = "https://login.microsoftonline.com/common"
API_LOCATION = "http://localhost:8000"
TOKEN_ENDPOINT = "/get_auth_token"
SCOPE = ["User.ReadBasic.All"]

###############################################################################
############################## MSAL Functions #################################
###############################################################################

def _load_cache():
    cache = msal.SerializableTokenCache()
    # if session.get("token_cache"):
    #     cache.deserialize(session["token_cache"])
    return cache

def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        CLIENT_ID, authority=authority or AUTHORITY,
        client_credential=CLIENT_SECRET, token_cache=cache)

def _build_auth_url(authority=None, scopes=None, state=None):
    return _build_msal_app(authority=authority).get_authorization_request_url(
        scopes or [],
        state=state,
        redirect_uri=API_LOCATION+TOKEN_ENDPOINT)

def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        return result


@app.get("/")
async def root(request: Request):
    auth_url = _build_auth_url(scopes=SCOPE,state="/homepage")
    return templates.TemplateResponse("login.html",{"request":request, "auth_url":auth_url})

@app.get("/get_auth_token")
async def get_auth_token(request: Request, code: str, state: str):
    if code!="":
        cache = _load_cache()
        cca = _build_msal_app(cache=cache)
        result = cca.acquire_token_by_authorization_code(
            code,
            scopes=SCOPE,  # Misspelled scope would cause an HTTP 400 error here
            redirect_uri=API_LOCATION + TOKEN_ENDPOINT)
        if "error" in result:
            raise HTTPException(status_code=400, detail="Unable to validate social login")
        token_to_encode = result.get("id_token_claims")
        accounts = cca.get_accounts()
        token = cca.acquire_token_silent(SCOPE,account=accounts[0])
        real_token = token["access_token"]
        print("real_token", real_token)

    else:
        raise HTTPException(status_code=400, detail="NO CODE GIVEN BY MICROSOFT")
    try :
        email = token_to_encode["preferred_username"]
        username = token_to_encode["preferred_username"]
    except:
        raise HTTPException(status_code=400, detail="Unsupported Email ID")
    return templates.TemplateResponse("microsoft_proxy.html", {"request":request, "redirect_url":state, "token":real_token, "username":username, "email":email})


@app.post("/add-microsoft-cookie")
async def get_token(request: Request):
    formdata = await request.form()
    # token = formdata["sub"]
    token = "EwBgA8l6BAAUAOyDv0l6PcCVu89kmzvqZmkWABkAAUv8KBFa9Wn3vjvz0ihgvLbvFTCI0UxYV2FMmhYnb8SFgoeGhdvoCofOfmYWkj0NjCmviICxCd7yhwi7EKSRkiS0NgB2Th3urpdtbwqaVpoXEeBYT98rEApojDGVVJgnkdskDd8XRR4yhRaY5U+Rp9O5bkn/P6pOa+iEYiTkhVZWVEdtoTCC6VCDTB0gMprZlnUV2DieW/hqoWLDGIkm2rHpCtOBAj1PzPLmoQXzM89xT6i6bPnhTsoZwsvVBp9KFvjwzp3kTQQwYCSHztV0YpbPFTGeHMKFzHnnFGy7F1MKYOvTBi+05vB0yI8TQU2dEK/wfgozrH8ettITjINQhWUDZgAACLBz+Vs9n9J6MALFsUkPxHOTjXfJMLwgwWGd5AZjaTxc63VKqC0Rqm5takl58o7x2Xps5pBp1n5G21yUKiA5JTwtaxkin6D1dhydzBqHUgy2g4FpULpL4wVcy7uZNFyM6tcHOLQkteHZVTZQHUWBhBYZhnp2n82UYFL0AZJohHwkm+llHPPM+fUuv7rB7MCG9Q5MiebEtcq7TlANw9Ic2xKAqWqVJXpf6++feBy2jmjOA9XEuC2La5nlKtKodNw62Gw6ZfMbjS8cH0xcaxIqtwByRwFPg5/+PHsZZu1xplQc4lxDLSD+rkAYBXAWfYwse1PCH024CqwhVnrjnKYIR5ju0t5r+3hkqWy/bT58+FuJcrlG3tSNSDObRXGdDc5Z2xLVxOIm1koyb4NdqIZlmCMqk80OVLV4PMPLezLuyh4SVPgtiqZI8XxVtSXPvvgUk0o0c1L++cFHNPzZBAORYBYUt6xmqaJyIdOR8106pjzqRGBaqg8InjOJgqH2ipo5YIRS7nCHhI+QgNuKHRKKVXWxFpVRKaCBrMwcRH8FrrwSHMYra366cEHiW6JUtsok/ks9Qmj8gwcWAxbuH67OYrM8PuKYuMEchslAECsmKd9HvO77c0vy+My6E0Ajxp1TplAQ5u4wVwn+f7hrvRYQr7W9jlhU+XQAOKEhEjpZ/dEblSWEU9dtZpdq+CUw2hjzDYEdMoPgYdgqL/97uez7WJv6e9pLAzP2o83IC3XFQa3vLoOqgn0qPbdPJHYC"

    response = JSONResponse({"access_token": token, "token_type": "bearer"})
    response.delete_cookie(key="Authorization", domain="localhost")
    response.set_cookie(
        key="Authorization",
        value=f"{token}",
        domain="localhost",
        httponly=True,
        max_age=3600,          # 1 hours
        expires=3600,          # 1 hours
    )
    print(token)
    return response

@app.get("/homepage")
async def homepage(request: Request):
    access_token = request.cookies.get("Authorization")
    headers = {
        'Authorization' : access_token,
        'Content-Type': 'application/json'
    }    
    response = rq.get("https://graph.microsoft.com/v1.0/me", headers = headers).json()
    print("response", response)
    return templates.TemplateResponse("homepage.html",{"request":request, "data":response})

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="http://localhost:8000/", status_code=303)
    response.delete_cookie(key="Authorization", domain="localhost")
    return response