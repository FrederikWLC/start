function message(status, shake=false, id="") {
  if (shake) {
    $("#"+id).effect("shake", {direction: "right", times: 2, distance: 8}, 250);
  } 
  document.getElementById("feedback").innerHTML = status;
  $("#feedback").show().delay(2000).fadeOut();
}
 $(document).on("click", "#connect-button", function() {
   console.log("Connect");
    $.post({
      type: "POST",
      url: "/connect",
      data: {"title": $("#title").val(),
             "content": $("#content").val()},
      success(response) {
        var status = JSON.parse(response)["status"];
        if (status === "Successfully sent") { location.reload(); }
        else{message(status, true, "connect-box");}
        
      }});
  });