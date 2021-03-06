'use strict';

var socket = null;
var isopen = false;

window.onload = function() {
    socket = new WebSocket('ws://127.0.0.1:9000');
    socket.binaryType = 'arraybuffer';

    socket.onopen = function() {
        console.log('Connected!');
        isopen = true;
    };

    socket.onmessage = function(e) {
        var tweet = JSON.parse(e.data);
        var el = document.getElementById('tweetlist');
        var li = document.createElement('li');
        var liked = tweet.like;
        var text = tweet.user + ': ' + tweet.text;

        li.appendChild(document.createTextNode(text));
        if (liked) {
            li.style.color = 'black';
        } else {
            li.style.color = 'gray';
        }
        el.appendChild(li);

        // if (typeof e.data === 'string') {
        //     console.log('Text message received: ' + e.data);
        // } else {
        //     var arr = new Uint8Array(e.data);
        //     var hex = '';
        //     for (var i = 0; i < arr.length; i++) {
        //       hex += ('00' + arr[i].toString(16)).substr(-2);
        //     }
        //     console.log('Binary message received: ' + hex);
        // }
    };

    socket.onclose = function(e) {
        console.log('Connection closed.');
        socket = null;
        isopen = false;
    };
};

function sendText() {
    if (isopen) {
        socket.send('Hello, world!');
        console.log('Text message sent.');
    } else {
        console.log('Connection not opened.');
    }
}

function sendBinary() {
    if (isopen) {
        var buf = new ArrayBuffer(32);
        var arr = new Uint8Array(buf);
        for (var i = 0; i < arr.length; ++i) {
            arr[i] = i;
        }
        socket.send(buf);
        console.log('Binary message sent.');
    } else {
        console.log('Connection not opened.');
    }
}

