import requests as req
import os
import keyboard

headers={
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
  }

path=os.getcwd()
#print(path)


class gift:

    def __init__(self,id,name,img) -> None:
        
        self.id=id
        self.name=name
        self.img_url=img
        self.img_path=self.get_img_path()

        pass

    def get_img_path(self):

        img=req.get(self.img_url,headers=headers)
        path_imgs=path+"\\gifts_imgs"

        if not os.path.exists(path_imgs):
            os.mkdir(path_imgs)

        img_name=path_imgs+"\\"+self.name+".png"

        if not os.path.isfile(img_name) :
            if img.status_code==200:
                with open(img_name,"wb") as f:
                    f.write(img.content)
                return img_name
            return None
        else:
            if os.stat(img_name).st_size<100:
                if img.status_code==200:
                    with open(img_name,"wb") as f:
                        f.write(img.content)
                    return img_name
                else:
                    return None
            else:
                return img_name
            
    @classmethod
    def get_gifts_img_path(cls,surch_str="",mode=1):
        all_gift_list=os.listdir("gifts_imgs")
        if mode==1:
            return all_gift_list
        if mode==2:
            rus_gift_list=[]
            for i in all_gift_list:
                if surch_str in i:
                    rus_gift_list.append(i)
            return rus_gift_list
        
def gift_mapping(mapping_keyboard_list):
    for i in mapping_keyboard_list:
        if not i == "":
            keyboard.press(i)
    for i in mapping_keyboard_list:
        if not i == "":
            keyboard.release(i)