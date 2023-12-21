from bilibili_api import live,Credential,user
import requests as req
import asyncio
import time
from gift import gift
import os
import json
import time
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import xml.dom.minidom
from bilibili_api import video, sync
import matplotlib.ticker as ticker

headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0',}
plt.rcParams['font.sans-serif'] = ['SimhEI']
# import matplotlib
# matplotlib.use('Agg')

credential = Credential(sessdata="af003eaf%2C1717054788%2Cf92bf%2Ac2CjBjPsDJyhLY0kWN8wGHQsJD4aT6ow1frhBsy82BkvaEjQm_kUHQTP7s8EHXxKZ6QxsSVkdTcU9XRDJzUlpVb1loV1M2angydUp0cUlvcnh1cVM3dnd5T2dBMGJ0TUcyOTdLeUZIQk1GMXRSTldHdHVRRWx3ZlRzeUpWVUJwVUxId3RsRDQ3alh3IIEC",
                        bili_jct="75a56a2fb99ada140f97e65b274fcd90",
                        buvid3="62D9D66B-3806-A08F-968D-D6D96FB1739829760infoc",
                        dedeuserid="32371455",
                        ac_time_value="9b5e659e1409280c3c4bb2401ffba7c2")

class bilibili:
    def __init__(self,signal=None) -> None:
        self.signal=signal
        pass


    def update_gift_list(self,room_id=None,area_id=None,area_parent_id=None):
        self.signal.logger.emit("开始获取礼物列表")
        all_gift=asyncio.run(live.get_gift_config(room_id,area_id=area_id,area_parent_id=area_parent_id))

        try:
            os.remove("gift_list.json")
        except:
            pass
        with open("gift_list.json","w") as f:
            b=json.dumps(all_gift)
            f.write(b)
        
        gift_list=[]
        gui_gift_list=[]
        for i in all_gift["list"]:
            pop_gift=False
            for k in ["弃",'测','废']:
                if k in i["name"]:
                    pop_gift=True
            if not pop_gift:
                one_gift=gift(i["id"],i["name"],i["img_basic"])
                gift_list.append(one_gift)
                gui_gift_list.append({"gift_name":i["name"],"gift_path":one_gift.img_path})
                time.sleep(0.1)
        return all_gift
    
    def update_area_list(self):
        area_list=asyncio.run(live.get_area_info())
        try:
            os.remove("area_list.json")
        except:
            pass
        with open("area_list.json","w") as f:
            b=json.dumps(area_list)
            f.write(b)

    async def isuid(self,uid):
        try:
            uid=int(uid)
            self.oneuser=user.User(uid,credential=credential)
            self.info=await self.oneuser.get_user_info()
            return True
        except:
            return False
            
    def get_user_name(self):
        return self.info['name']



class live_room():

    def __init__(self,room_id,signal) -> None:
        self.room_id=room_id
        self.room=live.LiveDanmaku(self.room_id,credential=credential)
        
        self.signal=signal
        self.connect_on()

    def connect(self):
        asyncio.run(self.room.connect())

    def connect_on(self):

        #@self.signal.room_connect.connect

        @self.room.on("DANMU_MSG")
        async def danmaku_msg(data):
            dm=data["data"]["info"][1]
            speaker=data["data"]["info"][2][1]
            self.signal.get_danmaku.emit(speaker,dm)
            #上面这行送到主程序

        @self.room.on("SEND_GIFT")
        async def get_gift(data):
            print(data["data"]["data"]['giftName'])
            ggift=data["data"]["data"]['giftName']
            self.signal.get_gift.emit(ggift)
            pass


class cangku():
    def __init__(self,uid=0):
        self.uid=uid
        self.url_series_id=''
        self.url_huifang_list=''
        
    def get_series_id(self):
        self.url_series_id="https://api.bilibili.com/x/series/series/all?mid={}&state=0&need_details=true".format(self.uid)
        res=req.get(self.url_series_id,headers=headers)
        time.sleep(2)
        series_id=''
        #print(res.json())
        for i in res.json()['data']['series_list']:
            #print(i)
            if i['meta']['name']=='直播回放':
                series_id=str(i['meta']['series_id'])
                #print(series_id)
        return series_id

    def get_huifang_str(self,page):
        huifang_str=''
        huifang_list=self.get_huifang_list(str(page))
        #print(str(huifang_list))
        n=(page-1)*10+1
        for i in huifang_list:
            #print(i)
            huifang_str+=str(n)+"."+i['title'][6:]+',{}dm/h\n'.format(int(danmu_min(i['bvid'])))
            n+=1
        if huifang_str!='':
            return huifang_str
        else:
            return '错误，请检查是否有直播回放'
        
    def get_huifang_list(self,page):
        self.url_huifang_list="https://api.bilibili.com/x/series/archives?mid={}&series_id={}&only_normal=true&sort=desc&pn={}&ps=10"
        series_id=self.get_series_id()
        self.url_huifang_list=self.url_huifang_list.format(self.uid,series_id,str(page))
        #print(self.url_huifang_list)
        huifang_list=req.get(self.url_huifang_list,headers=headers)
        #print(str(huifang_list.text))
        time.sleep(2)
        huifang_list=huifang_list.json()['data']['archives']
        return huifang_list
            

class ass():

    def __init__(self,signal=None,dm_path=None,bvid=None):
        # self.uid=uid
        self.signal=signal
        self.dm_path=dm_path
        self.bvid=bvid

    def get_bv_id(self,num,uid):
        page=int((int(num)-0.1)/10+1)
        ck=cangku(uid)
        huifang_list=ck.get_huifang_list(page)
        huifang_num=int(str(num)[-1])-1
        bv_id=huifang_list[huifang_num]['bvid']
        return bv_id

    def get_danmu_df(self,bv_id):
        v = video.Video(bvid=bv_id)
        dms =sync(v.get_danmakus(0))
        self.title = sync(v.get_info())
        self.title=self.title['title'][6:]
        columns = ['time','chat']
        all_danmu=[]
        for dm in dms:
            all_danmu.append({'time':str(dm.dm_time),'chat':str(dm.text)})
        danmu_df = pd.DataFrame(all_danmu, columns=columns)
        return danmu_df

    def ass_online_func(self):
        try:
            danmu_df=self.get_danmu_df(self.bvid)
            print(danmu_df)
        except:
            self.signal.ass_logger.emit("弹幕获取失败\n")
            return
        self.assmake(danmu_df,self.title)
        return

    def assmake(self,danmu_df,title):
        iszero=True
        while iszero:
            if int(float(danmu_df['time'].iloc[-1])) == 0:
                danmu_df = danmu_df[:-1]
            else:
                iszero=False
        sousuo=['草','ww','哈','?','事故','kksk','awsl','h','？','笑','好好','急急','别急','收米','有点','可爱','甜甜','kusa','离谱','卧槽']
        for i in range(len(danmu_df['time'].tolist())):
            danmu_df['time'][i]=int(int(danmu_df['time'][i][:danmu_df['time'][i].find('.')])/60)
        s_all=danmu_df['time'].value_counts().sort_index()
        #s_all.plot()
        s_sousuo=pd.Series([0]*int((len(s_all)*1.1)))
        for i in range(len(danmu_df['chat'])):
            for k in sousuo:
                if k in danmu_df['chat'][i]:
                    try:
                        s_sousuo[danmu_df['time'][i]]+=1
                    except:
                        pass
                    break
        mean=int(np.sqrt(s_sousuo.mean()*s_all.mean()))
        #一次滑动平均数据
        one_s=pd.Series(dtype=pd.Int32Dtype())
        one_s.loc[0]=0
        for i in range(len(s_all.tolist())-1):
            i+=1
            #print(i)
            try:
                one_s.loc[i]=int((s_all[i-1]+s_all[i]+s_all[i+1])/3)
            except:
                pass

        one_s_s=pd.Series(dtype=pd.Int32Dtype())
        one_s_s.loc[0]=0
        for i in range(len(s_all.tolist())-1):
            i+=1
            #print(i)
            try:
                one_s_s.loc[i]=int((s_sousuo[i-1]+s_sousuo[i]+s_sousuo[i+1])/3)
            except:
                pass
        kmean=np.array([])
        if one_s_s[one_s_s>=mean].values.tolist():
            s=one_s_s.sort_values(ascending=False, inplace=False)
            
            for i in range(15):
                i+=1
                x = np.array(s[s>=mean].keys())
                y = x.reshape(-1,1)
                km = KMeans(n_clusters=i,n_init='auto')
                cluster_=km.fit(y)
                kmean=km.cluster_centers_
                if cluster_.inertia_<one_s_s.keys()[-1]:
                    #print(kmean)
                    break

        #print(one_s)
        max_time=danmu_df['time'].iloc[-1]
        xl=int((max_time/3)/3)
        fig, (ax1, ax2) = plt.subplots(2, 1,figsize=(xl, 4))
        plt.subplots_adjust(wspace=1,hspace=1)

        

        ax1.plot(one_s)
        ax1.set_title(title)
        ax1.set_xlabel('time/(min)')
        ax1.set_ylabel('num')
        ax1.grid(True)
        ax1.set_xticks(np.arange(0, max_time, 3))  
        ax1.set_xlim(-5, max_time+5) 
        ax1.axhline(mean)

        dm_min=int(60*(len(danmu_df)/max_time))

        ax2.set_title('kensaku')
        ax2.plot(one_s_s)
        ax2.set_xlabel('AVERAGE:{}num/h,     time/(min)'.format(dm_min))
        ax2.set_ylabel('num')
        ax2.set_xticks(np.arange(0, max_time, 3))  
        ax2.set_xlim(-5, max_time+5) 
        ax2.grid(True) 
        ax2.axhline(mean)
        
        #ax3.plot(one_s)
        
        plt.savefig('gui/ass.png',dpi=85,bbox_inches = 'tight')

        plt.cla()
        point=''
        for i in kmean.astype('int').tolist():
            point+=str(i[0])+'，'
        if point=='':
            return '无'
        
        self.signal.ass_signals.emit(dm_min,point[:-1])
    
    def ass_xml(self):

        def get_danmu_df(danmu_path):
            dom=xml.dom.minidom.parse(danmu_path)
            root=dom.documentElement
            danmu_xml_list=root.getElementsByTagName("d")
            columns = ['time','chat']
            all_danmu=[]
            #print(len(danmu_xml_list))
            for dm in danmu_xml_list:
                p=dm.getAttribute("p")
                time=p[:p.find(",")]
                try:
                    dmtext=dm.firstChild.data
                except:
                    continue
                all_danmu.append({'time':time,'chat':dmtext})
            danmu_df = pd.DataFrame(all_danmu, columns=columns)
            return danmu_df
        
        try:
            danmu_df=get_danmu_df(self.dm_path)
        except:
            self.signal.ass_logger.emit("弹幕文件不兼容\n")
            return
        
        title=self.dm_path
        self.assmake(danmu_df,title)
        return

def danmu_min(bvid):
    from bilibili_api import video, sync
    a=video.Video(bvid=bvid)
    dms = sync(a.get_info())
    duration=dms['duration']
    dm_num=dms['stat']['danmaku']
    return 3600*dm_num/duration