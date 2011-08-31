
date=`date +%s`
channel='ch_teste'
id=${1:-1}
content="This is Spartaaaaaaa id=$id!!!"
post_data="{\"version\":\"1\",\"operation\":\"INSERT\",\"channelCode\":\"$channel\",\"reference\":\"0\",\"payload\":\"$content\",\"realtimeId\":\"$id\",\"dtCreated\":\"$date\"}"

curl -v "http://localhost:8080/broadcast/pub?ch=$channel&m=$id&t=$date" -d "rt_message=$post_data"
