"""商品名词 -> 商品图外链映射（按名词检索的电商官方商品图）。

每个名词 1~2 个外链，经典款 / 升级款轮换使用；URL 均来自阿里 / 京东 / 苏宁图床。
"""

IMAGES: dict[str, tuple[str, ...]] = {
    "5G 智能手机": (
        "https://img14.360buyimg.com/n1/jfs/t1/175048/1/5860/123768/608022ccE2b4258c4/5a3baca88ddcab1f.jpg",
        "https://img.alicdn.com/imgextra/i3/901751185/O1CN01hCnb3I1KcmICQlGEG_!!901751185.jpg",
    ),
    "轻薄折叠屏手机": (
        "https://imgservice.suning.cn/uimg1/b2c/image/uVEij1uWHqyr9whhr2EYOQ.jpg_400w_400h_4e",
        "https://imgservice.suning.cn/uimg1/b2c/image/zMzm_TBBhaOru4YXTSRTag.jpg_800w_800h_4e_80Q_is",
    ),
    "降噪蓝牙耳机": (
        "https://img.alicdn.com/i4/2200676337006/O1CN01EzKWHz21cnXdJLRHw_!!2200676337006.jpg",
        "https://img.alicdn.com/i2/2217587502021/O1CN01D17XOl1QnfTJIAFyW_!!2217587502021.jpg",
    ),
    "智能运动手表": (
        "https://img14.360buyimg.com/pop/jfs/t1/281865/10/8205/62211/67e14762Fdec2b6cb/3bb9b09f7aa9a918.jpg",
        "https://img30.360buyimg.com/n12/jfs/t235/136/1391473060/89726/e83a6fc8/53fadd9fN2eba4905.jpg!q70.jpg",
    ),
    "高清平板电脑": (
        "https://img.alicdn.com/i2/714625138/O1CN01Ng4o2S1npG0bMDUiS_!!714625138.jpg",
        "https://imgservice.suning.cn/uimg1/b2c/image/2r3OrT7GHWeNzs8IXIeWxQ.jpg_800w_800h_4e",
    ),
    "便携充电宝": (
        "https://img12.360buyimg.com/n1/jfs/t2587/135/1227408066/71924/557759a/5738a766N2d5fb9e1.jpg",
        "https://img12.360buyimg.com/n1/jfs/t2320/117/2184689816/85874/5cb8ade5/56c291e9N49b743fb.jpg",
    ),
    "无线充电器": (
        "https://img10.360buyimg.com/imgzone/jfs/t1/48783/12/17595/223026/627ba92bE993fadb4/3c0edb886ea0bc39.jpg",
        "https://cbu01.alicdn.com/img/ibank/2018/034/224/8810422430_438183670.jpg",
    ),
    "智能音箱": (
        "https://imgservice.suning.cn/uimg1/b2c/image/OeiCEm04Q_RteuOcpBSEjg.jpg",
        "https://img.alicdn.com/imgextra/i1/2211950259544/O1CN01pSr6G82KNCmtxRuX4_!!0-item_pic.jpg",
    ),
    "口袋运动相机": (
        "https://img.alicdn.com/bao/uploaded/O1CN01s6id8V1DZOB9GRWwI_!!6000000000230-2-yinhe.png",
        "https://img14.360buyimg.com/pop/jfs/t1/319727/25/8303/30445/684a7b6fF1d2f25d5/809083d7b220830c.jpg",
    ),
    "防摔手机壳": (
        "https://img11.360buyimg.com/n1/jfs/t2890/140/995126905/87335/74f9cc07/57300019N74c27916.jpg",
        "https://img14.360buyimg.com/n1/jfs/t2257/357/2316998519/147732/c317ecff/56d01017N7def3c6d.jpg",
    ),
    "轻薄笔记本电脑": (
        "https://img.alicdn.com/bao/uploaded/O1CN01ohRGF01hn4LbAJMIi_!!6000000004321-0-yinhe.jpg",
        "https://imgservice.suning.cn/uimg1/b2c/image/skmMNa7u8_30IF8dkUYuRg.jpg_800w_800h_4e",
    ),
    "高性能游戏本": (
        "https://p0.ssl.qhimgs1.com/t0119c95bf413bcadf4.jpg",
        "https://img.alicdn.com/bao/uploaded/O1CN01eFvSkK1ZcWPTRGUA9_!!6000000003215-2-yinhe.png",
    ),
    "商务办公台式机": (
        "https://img13.360buyimg.com/n1/jfs/t2545/243/1275979111/280752/6eeac0cc/569c55c1N49a0ae46.jpg",
        "https://imgservice.suning.cn/uimg1/b2c/image/pav4hMgMQkIgkQET_MqCYg.jpg_800w_800h_4e",
    ),
    "27 英寸显示器": (
        "https://img10.360buyimg.com/n0/g13/M02/1B/10/rBEhU1MegNIIAAAAAALMke1v0SAAAJ1ogDkwpkAAsyp962.jpg",
        "https://img30.360buyimg.com/shaidan/s720x540_jfs/t2170/360/977388621/111976/3345e22b/56374e24N3196a7cc.jpg",
    ),
    "机械键盘": (
        "https://img.alicdn.com/imgextra/i1/1070530219/O1CN01nJfB6n1DULLJUMldm_!!1070530219.jpg",
        "https://p1.ssl.qhimgs1.com/t01378c4fd1f97e6a97.jpg",
    ),
    "无线鼠标": (
        "https://img11.360buyimg.com/n1/g13/M01/12/19/rBEhUlJp4-gIAAAAAAFpHRNTdPsAAEkOwB0dWIAAWk1252.jpg",
        "https://img.alicdn.com/i4/407910984/TB2ltHscFXXXXacXpXXXXXXXXXX_!!407910984.jpg",
    ),
    "激光打印机": (
        "https://img11.360buyimg.com/n1/jfs/t1/177550/18/35586/29319/64c9f3efFac87c4d2/3966be7166971c61.jpg",
        "https://img14.360buyimg.com/pop/jfs/t1/312056/31/918/50026/6824a218Fa9ff25d3/a8f3d8a5b4d366b2.jpg",
    ),
    "移动固态硬盘": (
        "https://img12.360buyimg.com/n1/jfs/t1/275992/29/7737/53085/67de5229F3ee2d498/6cf33814753064d5.jpg",
        "https://img.alicdn.com/tfscom/i3/1968887547/TB2yMQimKuSBuNjSsziXXbq8pXa_!!1968887547.jpg",
    ),
    "视频会议摄像头": (
        "https://imgservice.suning.cn/uimg1/b2c/image/uNPPQuwRwoaylb-vu7D4ZA.jpg",
        "https://img30.360buyimg.com/popWareDetail/jfs/t1/122022/21/21237/89101/6269546aE1171b2a1/ff9f95aad36cada3.jpg",
    ),
    "人体工学椅": (
        "https://img10.360buyimg.com/n0/g16/M00/06/15/rBEbRlN0om0IAAAAAAIMj6WaFkIAABTSwFHbXgAAgyn348.jpg",
        "https://img13.360buyimg.com/n1/jfs/t3190/239/3468722826/304063/c9c3921d/57f468a7N6969a102.jpg",
    ),
    "多功能电饭煲": (
        "https://img14.360buyimg.com/n1/jfs/t2722/186/1967569587/126035/e057f0e9/57514ac0Nb134e6e1.jpg",
        "https://img11.360buyimg.com/n1/jfs/t3223/274/960365700/89087/cbe4ed65/57c38f04Naff42b60.jpg",
    ),
    "空气炸锅": (
        "https://cbu01.alicdn.com/img/ibank/2018/182/064/9462460281_439282807.400x400.jpg",
        "https://img.alicdn.com/imgextra/i2/312045056/O1CN01UE6YOG1nDh4XiIcCt_!!312045056.jpg_430x430.jpg",
    ),
    "破壁料理机": (
        "https://img13.360buyimg.com/n1/jfs/t2728/167/1163215463/174615/7e8a054e/5735b7bfN019fe235.jpg",
        "https://img14.360buyimg.com/n1/jfs/t1291/363/728722166/188758/bf239577/559e5066Nd6584dcf.jpg",
    ),
    "意式咖啡机": (
        "https://img14.360buyimg.com/pop/jfs/t1/239338/28/1003/51143/658a2cd9F00d81788/2deffdcfda024f2f.png",
        "https://img.alicdn.com/bao/uploaded/i1/2208339236869/O1CN01HbB7yR20c3Kwq5ehD_!!0-item_pic.jpg",
    ),
    "扫地机器人": (
        "https://img.alicdn.com/bao/uploaded/i5/TB1Xx2VHFXXXXaIXpXXuTH8FFXX_095015.jpg",
        "https://p0.ssl.qhimgs1.com/t012e1e8ac40539d63e.jpg",
    ),
    "无线吸尘器": (
        "https://img14.360buyimg.com/pop/jfs/t1/173479/21/33144/89155/639fe03cE6b3f3f59/30c914a5179b3f77.jpg",
        "https://p0.ssl.qhimgs1.com/t04eef0c8fd07363ea4.png",
    ),
    "智能空气净化器": (
        "https://img20.360buyimg.com/vc/g14/M08/11/05/rBEhV1MEUAAIAAAAAAMt4XglEJUAAI2MgDs0AMAAy35255.gif",
        "https://img14.360buyimg.com/pop/jfs/t1/183059/38/49878/255445/671c1ba2F8db31710/59fcdd759ecb368b.jpg",
    ),
    "变频空调": (
        "https://p0.ssl.qhimgs1.com/t0495274f9aa9fbfc0e.jpg",
        "https://img30.360buyimg.com/n1/jfs/t1/8150/11/14439/38101/5c651ba0Ebec9049c/59c621a8ef929b7e.jpg",
    ),
    "迷你洗衣机": (
        "https://img10.360buyimg.com/n1/jfs/t1675/149/557730414/289119/60fc5bce/55a8ae9aN9a5b9f70.jpg",
        "https://img10.360buyimg.com/n1/jfs/t1711/175/1438428804/126591/c59962f7/55ea81bcN24accf60.jpg",
    ),
    "电热水壶": (
        "https://img14.360buyimg.com/pop/jfs/t1/145199/27/24345/351604/6227199fE804e4926/4a927c74f6b6a1c1.png",
        "https://img.alicdn.com/bao/uploaded/i6/TB1cG6vKVXXXXb3XpXXUWaV.XXX_100459.jpg",
    ),
    "纯棉基础 T 恤": (
        "https://img30.360buyimg.com/popWaterMark/g14/M02/1E/15/rBEhV1NUj9oIAAAAAAIfnRE_5_AAAMUUgHVKbcAAh-1795.jpg",
        "https://img.alicdn.com/imgextra/i4/1901612258/TB2kE5PdC4mpuFjSZFOXXaUqpXa_!!1901612258.jpg",
    ),
    "轻薄羽绒服": (
        "https://img.alicdn.com/bao/uploaded/i2/TB1WEKpRVXXXXXxXXXXXXXXXXXX_!!0-item_pic.jpg",
        "https://img.alicdn.com/tfscom/i4/2246874252/TB1j.ULh_TI8KJjSsphXXcFppXa_!!0-item_pic.jpg",
    ),
    "休闲直筒牛仔裤": (
        "https://img.alicdn.com/tfscom/i1/1922532071/TB21FmWmFXXXXcuXXXXXXXXXXXX_!!1922532071.jpg",
        "https://img30.360buyimg.com/n12/jfs/t346/283/1286763811/304536/27ea297f/54363e7dN4bde16e6.jpg!q70.jpg",
    ),
    "法式连衣裙": (
        "https://img.alicdn.com/imgextra/i1/673785295/O1CN01PwPfkW1oz9qT9rlav_!!673785295.jpg",
        "https://img10.360buyimg.com/imgzone/jfs/t1/162767/36/12137/937148/604b23e8E2fd4793a/92344398e53133d5.jpg",
    ),
    "防风冲锋衣": (
        "https://img11.360buyimg.com/n12/jfs/t187/286/1154095164/212209/61dca72/53a3f25aNb5ae1552.jpg!q70.jpg",
        "https://img20.360buyimg.com/n12/jfs/t307/104/873333984/220473/adba0ad7/5427c37eN14dc78d9.jpg!q70.jpg",
    ),
    "轻便跑步鞋": (
        "https://img.alicdn.com/tfscom/i4/3296599130/TB2pM3LcjJTMKJjSZFPXXbHUFXa_!!3296599130.jpg",
        "https://img.alicdn.com/tfscom/i4/3296599130/TB2oa9tlBcHL1JjSZFBXXaiGXXa_!!3296599130.jpg",
    ),
    "真皮通勤皮鞋": (
        "https://img14.360buyimg.com/pop/jfs/t1/209898/8/18485/144650/621f6af4E7b5d1917/eda8289eb205cbf9.jpg",
        "https://img14.360buyimg.com/n5/s800x800_jfs/t3703/350/1772691993/42579/8ce1610a/58316c6aNe56cdf01.jpg",
    ),
    "大容量双肩包": (
        "https://img13.360buyimg.com/n12/jfs/t262/314/906927439/131157/d542f043/53f305a3N0085f3a3.jpg!q70.jpg",
        "https://img.alicdn.com/imgextra/i3/TB1mbF4KFXXXXXXXVXXXXXXXXXX_!!0-item_pic.jpg_430x430q90.jpg",
    ),
    "复古斜挎包": (
        "https://cbu01.alicdn.com/img/ibank/2014/160/160/1494061061_1590109343.jpg",
        "https://img13.360buyimg.com/n5/s800x800_jfs/t15547/56/1492267310/93971/2cba9bdf/5a5962f0N5e666ae9.jpg",
    ),
    "羊绒围巾": (
        "https://img14.360buyimg.com/imgzone/jfs/t1/342335/34/19106/113060/69022493F0e9eeeca/5723f8a81ecf9bec.jpg",
        "https://img11.360buyimg.com/n1/s720x720_jfs/t1/344966/22/19022/55489/6900b74bFd504c993/6514731fef305e05.jpg",
    ),
    "氨基酸洁面乳": (
        "https://img.alicdn.com/bao/uploaded/i3/2818013734/O1CN01wghNx41dSDOGJVqIr_!!0-item_pic.jpg",
        "https://img14.360buyimg.com/pop/jfs/t1/321085/8/9351/58232/684e9606F9f838296/c119af97023862e7.png",
    ),
    "烟酰胺精华液": (
        "https://img.alicdn.com/imgextra/i2/2452060795/TB22929fv2H8KJjy1zkXXXr7pXa_!!2452060795.jpg_2200x2200Q90s50.jpg",
        "https://img.alicdn.com/imgextra/i4/2452060795/TB2ZIhJq1uSBuNjy1XcXXcYjFXa_!!2452060795-0-item_pic.jpg_430x430q90.jpg",
    ),
    "保湿面霜": (
        "https://p0.ssl.qhimgs1.com/t013694c3c49b7674f0.jpg",
        "https://p2.ssl.qhimgs1.com/t0102ed6df7cdc2762c.jpg",
    ),
    "持妆粉底液": (
        "https://img13.360buyimg.com/n1/jfs/t1/89497/19/31020/17972/642f7f94F94657982/2cb9e3fe62471579.jpg",
        "https://imgservice.suning.cn/uimg1/b2c/image/dvPzMYPzWTyHPLpOZ01-Sw.jpg",
    ),
    "丝绒口红": (
        "https://img.alicdn.com/tfscom/i4/302149964/TB2XXrFiSBjpuFjSsplXXa5MVXa_!!302149964.jpg",
        "https://img.alicdn.com/imgextra/i2/57605890/O1CN01Rcavkm1tNfZ61nzRJ_!!57605890.jpg",
    ),
    "防晒喷雾": (
        "https://img.alicdn.com/tfscom/i4/95261292/TB2EB4mfruWBuNjSszgXXb8jVXa_!!95261292.jpg",
        "https://img13.360buyimg.com/n5/s450x450_jfs/t16996/21/1558770550/226331/91d7e937/5acdb54eN1d1f85cc.jpg",
    ),
    "修护洗发水": (
        "https://img.alicdn.com/tfscom/i1/2371697090/TB2ypZHzNlmpuFjSZPfXXc9iXXa_!!2371697090.jpg",
        "https://img.alicdn.com/imgextra/i3/2168464600/O1CN018gumTm1jqqZqhmMVf_!!2168464600.jpg_400x400.jpg",
    ),
    "木质调香水": (
        "https://img.alicdn.com/imgextra/i1/2211897678985/O1CN01YNSPsm2GFBM55zOfE_!!2211897678985.jpg",
        "https://img.alicdn.com/imgextra/i4/2208576100743/O1CN01eUuhYk1HMKyK27vZ5_!!2208576100743.jpg",
    ),
    "电动牙刷": (
        "https://img30.360buyimg.com/popWaterMark/jfs/t1/19124/20/9556/53171/5c8085afEb4030c65/8d8e13ac2c313bb7.jpg",
        "https://p0.ssl.qhimgs1.com/t01a0b555bf0382ced0.jpg",
    ),
    "蒸汽眼罩": (
        "https://img.alicdn.com/i4/1827024447/O1CN016C2KDl1iim18sUY7O_!!1827024447.jpg",
        "https://img.alicdn.com/tfscom/i4/4254811811/O1CN01Im54U41PFTkzK8Vk5_!!0-item_pic.jpg",
    ),
    "每日坚果礼盒": (
        "https://img14.360buyimg.com/pop/jfs/t1/117257/6/39037/197645/646ed491F0f920887/6f8538cf5f0294db.png",
        "https://img10.360buyimg.com/n1/jfs/t2050/195/1781812593/529575/c3d623a6/56d928aeN4c648470.jpg",
    ),
    "手工曲奇饼干": (
        "https://img.alicdn.com/i2/3258320662/TB2i3AXi3aTBuNjSszfXXXgfpXa_!!3258320662.jpg",
        "https://img.alicdn.com/bao/uploaded/i3/3258320662/TB2x.ABiVOWBuNjy0FiXXXFxVXa_!!3258320662.jpg",
    ),
    "原切牛肉干": (
        "https://img13.360buyimg.com/n1/jfs/t3049/18/6010596645/107498/9aa93af0/5895a65dN47c80314.jpg",
        "https://img13.360buyimg.com/n1/g15/M01/0E/1F/rBEhWVMqaW4IAAAAAAQyeixJy90AAKYlgIl59IABDKS443.jpg",
    ),
    "黑巧克力": (
        "https://cbu01.alicdn.com/img/ibank/2018/264/905/8570509462_1283446595.jpg",
        "https://imgservice.suning.cn/uimg1/b2c/image/mhYRMZ76UL1QpCu6cAODzQ==.jpg_800w_800h_4e",
    ),
    "五常大米": (
        "https://img14.360buyimg.com/pop/jfs/t1/239897/40/10980/143261/66699361Fd2669b2e/e4ee78cb654d4483.png",
        "https://p1.ssl.qhimgs1.com/t0103cc55f288a2d041.jpg",
    ),
    "初榨橄榄油": (
        "https://img10.360buyimg.com/n1/g14/M07/15/1A/rBEhV1MZidQIAAAAAAPfOE98-bkAAJwYQNpGdcAA99Q217.jpg",
        "https://img.alicdn.com/imgextra/i3/2211582425643/O1CN01vjmg9E1rYXjHipl2B_!!2211582425643-0-scmitem1000.jpg",
    ),
    "冷冻虾仁": (
        "https://img.alicdn.com/tfscom/i2/1693154484/TB2ir49d4OMSKJjSZFlXXXqQFXa_!!1693154484.jpg",
        "https://img.alicdn.com/i2/442685351/TB2FrxTsNuTBuNkHFNRXXc9qpXa_!!442685351.jpg",
    ),
    "云南小粒咖啡": (
        "https://img.alicdn.com/i4/124438855/TB2hBxQapqZBuNjt_jqXXamzpXa_!!124438855.jpg",
        "https://img.alicdn.com/tfscom/i3/124438855/TB2jVTekLNNTKJjSspfXXbXIFXa_!!124438855.jpg",
    ),
    "高山绿茶": (
        "https://cbu01.alicdn.com/img/ibank/2019/320/805/11697508023_1994561742.jpg",
        "https://img10.360buyimg.com/n1/jfs/t2800/2/1107629885/226319/9a82b69c/573435deNc85691c0.jpg",
    ),
    "有机纯牛奶": (
        "https://img.alicdn.com/bao/uploaded/O1CN018S1kqN1d0Hdj8121f_!!6000000003673-0-yinhe.jpg",
        "https://img.alicdn.com/imgextra/i1/1657488384/O1CN01B2PjJG2BnvO2e2vDL_!!1657488384.jpg",
    ),
    "专业瑜伽垫": (
        "https://img.alicdn.com/tfscom/i1/1658641505/TB2DgehqYuWBuNjSszgXXb8jVXa_!!1658641505-0-item_pic.jpg",
    ),
    "可调节哑铃": (
        "https://img13.360buyimg.com/n1/jfs/t2932/5/230883188/444565/658e854a/57506063N9dc92659.jpg",
        "https://img12.360buyimg.com/n1/jfs/t1723/117/373128903/224903/86355a0/55cfdde9N4307678e.jpg",
    ),
    "碳纤维羽毛球拍": (
        "https://img.alicdn.com/i4/2276766026/TB2pFk6XX55V1Bjy0FnXXc5XFXa_!!2276766026.jpg",
        "https://img.alicdn.com/i2/1730471070/TB2OWGXbrH9F1JjSZFBXXc9ZFXa_!!1730471070.jpg",
    ),
    "竞速跳绳": (
        "https://img.alicdn.com/i2/2181757918/TB2Benlj5MnBKNjSZFzXXc_qVXa_!!2181757918.jpg",
        "https://img14.360buyimg.com/pop/jfs/t1/235444/1/20790/98506/668371a5F35f5ae5f/796a1c52abb0961f.png",
    ),
    "露营帐篷": (
        "https://img13.360buyimg.com/n1/jfs/t154/262/519718903/224603/8a868687/539046a6Na25c4e9b.jpg",
        "https://img11.360buyimg.com/n1/jfs/t2536/304/1315756987/219388/533f1be2/56af428fNaf4c7bc4.jpg",
    ),
    "户外折叠椅": (
        "https://img11.360buyimg.com/n12/jfs/t187/68/1262703769/228253/28fc4656/53aa20dbNa63a4dcc.jpg!q70.jpg",
        "https://img11.360buyimg.com/n12/jfs/t169/138/2156694842/452889/c4c82337/53c63184Naff97b52.jpg!q70.jpg",
    ),
    "登山背包": (
        "https://img.alicdn.com/i1/15592829/T2MThHX1haXXXXXXXX_!!15592829.jpg",
        "https://img10.360buyimg.com/n0/g16/M00/02/18/rBEbRlNsU7QIAAAAAASA_ejx-EcAAAirgMPUosABIEV193.png",
    ),
    "保温运动水壶": (
        "https://img14.360buyimg.com/n1/g7/M03/12/16/rBEHZlD2kEUIAAAAAANUeU5-zlUAADpsgN7CRkAA1SR154.jpg",
        "https://img11.360buyimg.com/n1/jfs/t3073/205/2916433171/351060/90cf2065/57e88c85Nbb653f32.jpg",
    ),
    "骑行头盔": (
        "https://cbu01.alicdn.com/img/ibank/2015/513/056/2071650315_1902088033.jpg",
        "https://img30.360buyimg.com/popWaterMark/g10/M00/1C/17/rBEQWFNct4gIAAAAAAiwO0Mp-WgAAFocAG7dtwACLBT879.jpg",
    ),
    "防滑徒步鞋": (
        "https://img20.360buyimg.com/n12/jfs/t331/285/382479999/357062/42c8f137/540fb4dfN755b77e6.jpg!q70.jpg",
        "https://img10.360buyimg.com/n1/jfs/t1990/197/1512304707/178496/396fad82/56614654Na74814f9.jpg",
    ),
    "数据分析入门图书": (
        "https://img14.360buyimg.com/n1/jfs/t2665/51/434502103/41061/b8b52d44/57130bb1N5dbdcb52.jpg",
        "https://img13.360buyimg.com/n1/jfs/t2815/107/1364002929/81096/8a790a5/573d8c0aNeeb6c94e.jpg",
    ),
    "人工智能通识读本": (
        "https://img14.360buyimg.com/pop/jfs/t1/320040/18/20661/64755/6890925fF79b04a58/1d2efe33900afc42.jpg",
        "https://img14.360buyimg.com/pop/jfs/t1/194879/13/43397/39836/665bca5aFba3f9b93/c94d10eca5a46356.jpg",
    ),
    "经济学经典套装": (
        "https://img14.360buyimg.com/n1/jfs/t3223/111/1945956264/245069/61b6587c/57d793fdN0c913aab.jpg",
        "https://img10.360buyimg.com/n1/jfs/t2290/204/2015521590/94476/e16a272e/56eb5dc2Nf2f2bfbc.jpg",
    ),
    "儿童绘本套装": (
        "https://img14.360buyimg.com/pop/s500x500_jfs/t1/16869/25/6028/1733337/5c48278fE79f5d840/8f675cb24897ec61.jpg",
        "https://img13.360buyimg.com/n1/jfs/t3625/155/1356214042/472494/74e67818/5822dac4N5d232f20.jpg",
    ),
    "钢笔礼盒": (
        "https://imgservice.suning.cn/uimg1/b2c/image/GitwEWzazyV8_fsxQ0P0_Q.jpg_800w_800h_4e",
        "https://img.alicdn.com/i4/TB1nLOHNpXXXXcXXXXXXXXXXXXX_!!0-item_pic.jpg",
    ),
    "手账本套装": (
        "https://img14.360buyimg.com/pop/jfs/t1/166199/27/46304/321543/664abb68F1ed6d926/0818471f2f2a10fb.jpg",
        "https://imgservice.suning.cn/uimg1/b2c/image/-dIuwuPQxZHLM9pA4NJVaQ.jpg_800w_800h_4e",
    ),
    "入门尤克里里": (
        "https://img13.360buyimg.com/n1/jfs/t1/20401/9/8294/36840/5c74b635E339897b9/d53eb5f40afeaff5.jpg",
        "https://img14.360buyimg.com/pop/jfs/t1/220009/27/12793/199472/6211dab0Edd14893a/d22445879c6bd440.jpg",
    ),
    "便携蓝牙音箱": (
        "https://img13.360buyimg.com/n1/jfs/t2728/29/3981136574/325243/a0a0fb0c/57a3f10eN48de7925.png",
        "https://img11.360buyimg.com/n1/jfs/t2428/268/2470168776/198967/84772e71/56dae18dN071d9136.jpg",
    ),
    "桌面护眼台灯": (
        "https://img14.360buyimg.com/n1/jfs/t406/12/291322036/234333/7ed4eadf/54145dccN9412663a.jpg",
        "https://cbu01.alicdn.com/img/ibank/O1CN01IDmJXk2D8MZtYhLDO_!!3533158564-0-cib.jpg",
    ),
    "城市建筑拼图": (
        "https://img14.360buyimg.com/n1/jfs/t3400/110/1503423273/125203/ffd63e88/5826a470Nafcd0b39.jpg",
        "https://img14.360buyimg.com/pop/jfs/t1/187025/15/43901/147094/669ccab4F8efaa2fb/6c790ec0fddd017c.jpg",
    ),
    "婴儿纸尿裤": (
        "https://img.alicdn.com/tfscom/i1/1672731343/TB2lRfyaqi5V1BjSsphXXaEpXXa_!!1672731343.jpg",
        "https://cbu01.alicdn.com/img/ibank/2020/224/616/14822616422_2109937442.jpg",
    ),
    "婴幼儿奶粉": (
        "https://img14.360buyimg.com/pop/jfs/t1/280603/29/16879/89772/67f88519Fe40b87cf/14515827be710599.png",
        "https://img.alicdn.com/i1/725677994/TB2hFvoppuWBuNjSspnXXX1NVXa_!!725677994.jpg",
    ),
    "宝宝辅食机": (
        "https://img.alicdn.com/bao/uploaded/i2/TB1xeoTIFXXXXbgXXXXXXXXXXXX_!!0-item_pic.jpg_430x430q90.jpg",
        "https://img.alicdn.com/i1/2201202034877/O1CN01offx7Y1lti8g2yLnr_!!2201202034877.jpg_300x300q90.jpg",
    ),
    "儿童安全座椅": (
        "https://img12.360buyimg.com/n1/jfs/t18082/327/1792973934/107234/5250c048/5ad8ab6bNf044ba42.jpg",
        "https://imgservice.suning.cn/uimg1/b2c/image/KM22aX2GUH_HdEsfPKmhGg.jpg_800w_800h_4e",
    ),
    "益智积木套装": (
        "https://img11.360buyimg.com/n1/jfs/t2764/350/3363263200/385827/507d436a/5788a928N6d26218a.jpg",
        "https://img13.360buyimg.com/n1/g9/M03/05/00/rBEHalBCD4oIAAAAAAQRB_qR1DgAAA-xQNm3iEABBEf244.jpg",
    ),
    "遥控越野车": (
        "https://img13.360buyimg.com/n1/jfs/t2656/78/874681919/142995/aa09c1a3/572aa89eN983a3fa7.jpg",
        "https://img10.360buyimg.com/n1/jfs/t2086/63/2122783706/249460/26dae62c/56aacb84N72568fcf.jpg",
    ),
    "柔软毛绒玩偶": (
        "https://img14.360buyimg.com/pop/jfs/t1/102714/38/52057/213464/670df0e1Ff7545e7d/d5441b5700d8c8a0.jpg",
        "https://img.alicdn.com/imgextra/i4/3984573045/O1CN01XBhHWY1YMemc2g4Ty_!!3984573045.jpg",
    ),
    "科学实验套装": (
        "https://img.alicdn.com/imgextra/i4/2208010877214/O1CN01iBVcIh23A3zY3JLp9_!!2208010877214.jpg",
        "https://img.alicdn.com/bao/uploaded/i1/4259330643/O1CN01yVZg5n1GcXJUUJZY0_!!0-item_pic.jpg",
    ),
    "儿童平衡车": (
        "https://imgservice.suning.cn/uimg1/b2c/image/z7NWdLBVdKjqwjVLLawHeA.jpg_800w_800h_4e",
        "https://cbu01.alicdn.com/img/ibank/2019/181/631/10355136181_407121079.jpg",
    ),
    "亲子桌游": (
        "https://img.alicdn.com/i1/70760630/O1CN016VymPp1GWaGUAHzLO_!!70760630.jpg",
        "https://img.alicdn.com/tfscom/i1/428678986/TB2MElZluOSBuNjy0FdXXbDnVXa_!!428678986.jpg",
    ),
    "北欧布艺沙发": (
        "https://img11.360buyimg.com/n1/jfs/t2851/33/1251193086/197281/d603dcf/57397ffdNf3ca5387.jpg",
        "https://img14.360buyimg.com/n12/jfs/t169/25/1255188276/514440/71d8492/53a7d66aN243e3741.jpg!q70.jpg",
    ),
    "实木餐桌": (
        "https://img20.360buyimg.com/n12/g15/M0A/00/07/rBEhWFHee-sIAAAAAALAxuVAoUYAAA9PwPYO9oAAsDe538.jpg!q70.jpg",
        "https://img.alicdn.com/bao/uploaded/i1/TB1XuUAKpXXXXXBXXXXXXXXXXXX_!!0-item_pic.jpg_430x430q90.jpg",
    ),
    "天然乳胶床垫": (
        "https://img11.360buyimg.com/n1/jfs/t3157/82/3442489167/172335/ae62a7c1/57f3566fN5d59a15a.jpg",
        "https://img12.360buyimg.com/n1/g12/M00/00/1A/rBEQYVMqZfAIAAAAAAVUqCx1o30AAC_ewJxTlEABVTA783.jpg",
    ),
    "遮光窗帘": (
        "https://img.alicdn.com/tfscom/i2/2454336108/TB1AJ0hoAOWBuNjSsppXXXPgpXa_!!0-item_pic.jpg",
    ),
    "羊毛地毯": (
        "https://img.alicdn.com/bao/uploaded/i4/TB2gBXKmCBjpuFjy1XdXXaooVXa_!!134939182.jpg",
        "https://img13.360buyimg.com/n1/jfs/t27259/333/1682455026/292276/f1ad90c7/5be850bcN61f5eb32.jpg",
    ),
    "LED 吸顶灯": (
        "https://img30.360buyimg.com/n12/jfs/t169/364/2998522660/194003/7d745275/53df3176N31d5e80d.jpg!q70.jpg",
        "https://img30.360buyimg.com/n1/jfs/t1/107568/8/30680/28574/63e4635bFa7243c8d/e9ab14d4d98acead.jpg",
    ),
    "智能门锁": (
        "https://p2.ssl.qhimgs1.com/t04278a33df894e59d2.jpg",
        "https://p2.ssl.qhimgs1.com/t046b90b12e42eb291c.jpg",
    ),
    "恒温花洒": (
        "https://img.alicdn.com/i3/2924806077/O1CN011ulJLWKwzaM7UT8_!!2924806077.png",
        "https://img10.360buyimg.com/n1/g14/M01/05/06/rBEhVlHiEUAIAAAAAAC-XCJERSIAABBAQFs7oIAAL50197.jpg",
    ),
    "收纳边柜": (
        "https://img14.360buyimg.com/n1/jfs/t2677/324/1598446877/299081/802932f1/574402f8N762df77d.jpg",
        "https://img.alicdn.com/tfscom/i3/TB1.B.IXxHBK1JjSZFkYXHg9VXa_M2.SS2",
    ),
    "香薰蜡烛": (
        "https://p2.ssl.qhimgs1.com/t0164e805c5cb7acca2.jpg",
        "https://img.alicdn.com/tfscom/i4/2164468476/TB2Gjp0a1LyQeBjy1XaXXcexFXa_!!2164468476.jpg",
    ),
}
