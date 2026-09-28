## This is the Example of how to called Taffy Fondue API beside opennyc drain_category
## What I need is about transient Flooding in Bnagkok Area.


Resource URL
https://publicapi.traffy.in.th/share/search?hashtag=โรงพยาบาลสนาม&offset=0


Resource Information
Response formats	JSON
Requests limit per minute	100

Parameters
Name	Required	Description	Default Value	Example
hashtag	require	Hashtag ที่ต้องการค้นหา	 	ศูนย์ฉีดวัคซีน
keyword	optional	คำค้น ที่ต้องการค้นหา	 	ตำแหน่งศูนย์ฉีดวัคซีน บางซื่อ
offset	optional	กำหนดค่าเริ่มต้นของข้อมูล	0	5

{
  status: true,
  total: 3,
  results: [
    {
      hashtag: [
        "#โรงพยาบาลสนาม"
      ],
      description: "#โรงพยาบาลสนาม ชัยภูมิ แห่งที่ 1",
      photo: "https://storage.googleapis.com/traffy_public_bucket/chat-bot-img/thaithealth-photos/14549775686038.jpeg",
      coord: [
        102.02051115063,
        15.807776225599,
      ],
      timestamp: "2021-08-10 17:34:35.342993+00",
      address: "สนามกีฬากลางจังหวัดชัยภูมิ Thailand",
    },
    {
      hashtag: [
        "#โรงพยาบาลสนาม"
      ],
      description: "#โรงพยาบาลสนาม โคราชแห่งที่ 2",
      photo: "https://storage.googleapis.com/traffy_public_bucket/chat-bot-img/thaithealth-photos/14549755585978.jpeg",
      coord: [
        102.046614,
        14.926116,
      ],
      timestamp: "2021-08-10 17:19:44.792957+00",
      address: "อาคารลิปตพัลลภ Thailand",
    },
    {
      hashtag: [
        "#โรงพยาบาลสนาม"
      ],
      description: "#โรงพยาบาลสนาม โคราช",
      photo: "https://storage.googleapis.com/traffy_public_bucket/chat-bot-img/thaithealth-photos/14549741188425.jpeg",
      coord: [
        102.047441,
        14.926127,
      ],
      timestamp: "2021-08-10 17:14:25.516962+00",
      address: "อาคารชาติชาย ฮออล์ สนามกีฬา 80 พรรษา Thailand",
    },
  ],
}