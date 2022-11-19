import cloudinary
import requests
import cloudinary.uploader as uploader



class CloudStorage:
    def __init__(self):
        cloudinary.config( 
            cloud_name = "dab2kopjh", 
            api_key = "221928939994312", 
            api_secret = "FvW3lyjWZF6ECYEWPdnHETip3C4" 
        )
    
    def upload(self,filePath):
        result = cloudinary.uploader.upload(
            filePath, 
            folder = "cctv/", 
            public_id = filePath,
            overwrite = True, 
            resource_type = "video"
        )

        try:
            return result['error']
        except:
            return "Upload Success"

    def delete(self,filePath):
        result = cloudinary.uploader.destroy(
            "cctv/"+filePath,
            resource_type = "video"
        )
        try:
            return result['error']
        except:
            return "Delete Success"

def main():
    storage = CloudStorage()
    result = storage.upload("cam1_2022-11-19230818-f.mp4")
    print(result)

if __name__ == "__main__":
    main()


    