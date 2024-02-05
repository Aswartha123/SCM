from fastapi import FastAPI, File,Request,Form,Depends,HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from bson.objectid import ObjectId
from passlib.context import CryptContext 
from datetime import datetime,timedelta
import jwt
import smtplib
import random
import string





app = FastAPI()
templates = Jinja2Templates(directory="newtemplates")

client = MongoClient("mongodb+srv://Aswartha:aswartha@cluster0.brhrhhb.mongodb.net/")

database= client.get_database("Students")
collection= database.new
devicedata= database.device_data
shipment=database.shipments

SECRET_KEY="24062005"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="token")
pwd=CryptContext(schemes=["bcrypt"],deprecated="auto")

app.mount("/static",StaticFiles(directory="static"),name="static")

#    user-defined functions
    
    #verfiy the password passord with hased password from the database
def verify_password(plain_password, hashed_password):
    return pwd.verify(plain_password, hashed_password)

# hasing the password
def get_password_hash(password):
    return pwd.hash(password)

# creating a token with the user email
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt =(jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))

    return encoded_jwt 


@app.post("/user_data")
async def user_data(request:Request,data:dict):
    user_token=data['token']
    try:
        payload = jwt.decode(user_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = collection.find_one({"email": username},{"_id":0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")

# pages redirecting functions   
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("loginfrom.html",{"request":request})

@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("loginfrom.html",{"request":request})

@app.get("/signup")
async def signup(request: Request):
    global captcha
    # captcha=catcha()
    captcha = ''.join(random.choices(string.ascii_uppercase + string.digits+string.ascii_lowercase+string.punctuation, k=8))
    return templates.TemplateResponse("signup.html",{"request":request,"captch":captcha})

@app.get("/forgot")
async def forgot(request: Request):
    return templates.TemplateResponse("forgot.html",{"request":request})
 
  
#user signup 
@app.post("/signup")
async def signup(request: Request,username: str = Form(),password: str =Form(),email: str=Form(),con_password:str=Form(),captch:str = Form()):
    if  collection.find_one({"email": email}):
        if password==con_password:
            if captcha==captch:
                password=get_password_hash(password)
                data={"username":username,"email":email,"password":password,"role":"user"}
                collection.insert_one(data)
                return templates.TemplateResponse("loginfrom.html",{"request":request})
            else:
                return{"reenter the captcha"}
        else:
            return{"password and confirm password are not same"}
    else:
        return{"this email have a user account"}


#image inserting into database
@app.post("/image")
async def add_blog(request:Request,images:UploadFile=File(),email:str=Form()):
        user=collection.find_one({"email":email})
        imagepath="static/images/"
        path=f"{imagepath}{images.filename}"
        image_data=await images.read()
        with open(path,'wb') as blogs_images:
            blogs_images.write(image_data)
        collection.update_one(user,{"$set":{"profile":path}})
        
#user login      
@app.post("/loginto")
def find(request: Request,email: str = Form(),password: str =Form()):
    details= collection.find_one({"email":email})
    if details:
        if verify_password(password,details['password']):
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(data={"sub": email}, expires_delta=access_token_expires)

            return templates.TemplateResponse("dashboard.html",{"request":request,"message": "Logged in successfully", "access_token": access_token})
        else:
            return {"error": "Wrong password"}
    else:
         return{"user doesn't exsit"}
    

#user logout       
# @app.post("/logout",response_class=HTMLResponse)
# def logout(request:Request):
#     return templates.TemplateResponse("loginfrom.html",{"request":request})


# forgot password

#sending otp through the email using smtp lib
@app.post("/otp",response_class=HTMLResponse)
def forgot_password(request: Request,email: str= Form()):
    user = collection.find_one({"email": email})
    global main_email
    main_email=email
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    otp = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    user["otp"] = otp
    collection.update_one({"_id": ObjectId(user["_id"])}, {"$set": user})

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("pailaaswartha1@gmail.com","rcyr lymk ummi uizd")
    message = 'Subject: {}\n\n{}'.format('OTP for password reset', 'Your OTP is: ' +otp)
    server.sendmail("pailaaswartha1@gmail.com", user["email"], message)
    server.quit()
    return templates.TemplateResponse("otp.html",{"request":request})


# verfiy the otp from the database
@app.post("/verify",response_class=HTMLResponse)
def verify(request:Request,otp:str=Form()):
    email=main_email
    use = collection.find_one({"email":email})
    if use["otp"]==otp:
        return templates.TemplateResponse("new_password.html",{"request":request})
    else:
        raise HTTPException(status_code=400,detail="wrong otp") 


# updating the new password
@app.post("/new_password",response_class=HTMLResponse)
def new_password(request:Request,password:str=Form(),con_password:str=Form()):
    mail=main_email
    user = collection.find_one({"email":mail})
    if password==con_password:
           user["password"]=get_password_hash(password)
           result=collection.update_one({"_id": ObjectId(user["_id"])}, {"$set": user})

    if not result:
        return{"try again"}
    else:
        return templates.TemplateResponse("loginfrom.html",{"request":request})


#inserting the new shipment details into database
@app.post("/create_shipment")  
async def ship(request: Request,email: str= Form(),shipment_number: str = Form(),route_details: str =Form(),device: str=Form(),ndc_number:str=Form(),serial_number:str = Form(),po_number:str=Form(),
                   container_number:str = Form(),goods_type:str = Form(),delivery_date:str = Form(),delivery_number:str = Form(),batch_id:str = Form(),description:str = Form()):

        if shipment.find_one({"shipment_number":shipment_number}):
            return{"shipment number already exsits"}
        else:
            data={"email":email,"shipment_number":shipment_number,"route_details":route_details,"device":device,"ndc_number":ndc_number,"serial_number":serial_number,"po_number":po_number,
                "container_number":container_number,"goods_type":goods_type,"delivery_date":delivery_date,"delivery_number":delivery_number,"batch_id":batch_id,"description":description}
            shipment.insert_one(data)
            return{"successfully created"}
        
@app.post("/my_shipments")
async def user_data(request:Request,data:dict):
    user_email=data['email']
    if collection.find_one({"email":user_email}):
           shipments=list(shipment.find({"email":user_email},{'_id':0}))
           return shipments
    
@app.post("/device_data")
async def device_data(request:Request,data:dict):
     user_email=data['email']
     user_data=collection.find_one({"email":user_email})
     if user_data["role"]=="admin":
          data=list(devicedata.find({},{'_id':0}))
          return data
     else:
         return {""}
