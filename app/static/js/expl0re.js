function message(status, shake=false, id="") {
  if (shake) {
    $("#"+id).effect("shake", {direction: "right", times: 2, distance: 8}, 250);
  } 
  document.getElementById("feedback").innerHTML = status;
  $("#feedback").show().delay(2000).fadeOut();
}
 $(document).on("click", "#explore-button", function() {
   console.log("Explore");
    $.post({
      type: "POST",
      url: "/explore",
      data: {"radius": $("#radius").val(),
             "location": $("#location").val()},
      success(response) {
        var status = JSON.parse(response)["status"];
        if (status === "Successfully validated") { location.reload(); }
        else{message(status, true, "explore-box");}
        
      }});
  });