
channel='ch_teste'
id=${1:-1}

curl -v "http://localhost:8080/broadcast/sub?ch=$channel&m=$id&s=M"
