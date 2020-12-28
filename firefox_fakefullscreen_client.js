// inject into firefox web pages with a code injector addon or similar
document.onfullscreenchange = function ( event ) {
    console.log("fullscreen change")
    console.log(document.fullscreen);
    var oReq = new XMLHttpRequest();
    if (document.fullscreen)
        oReq.open("get", "http://localhost:8000/maxon", true);
    else
        oReq.open("get", "http://localhost:8000/maxoff", true);
    oReq.send();
};
