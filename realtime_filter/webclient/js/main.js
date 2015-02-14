'use strict';

function reqListener() {
    console.log(this.responseText);
}

function like(id) {
    var req = new XMLHttpRequest();
    //req.onreadystatechange = reqListener();
    req.open('POST', '/tag/like');
    req.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    req.send(JSON.stringify({
        id: id
    }));
}

function dislike(id) {
    var req = new XMLHttpRequest();
    //req.onreadystatechange = reqListener();
    req.open('POST', '/tag/dislike');
    req.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    req.send(JSON.stringify({
        id: id
    }));
}

function clearPreference(id) {
    var req = new XMLHttpRequest();
    //req.onreadystatechange = reqListener();
    req.open('POST', '/tag/clear');
    req.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
    req.send(JSON.stringify({
        id: id
    }));
}
