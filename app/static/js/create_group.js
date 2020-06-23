function message(status, box_id, shake=false) {
  $("#feedback-"+box_id).stop(stopAll=true);
document.getElementById(box_id+"-anchor").scrollIntoView(false);

  if (shake) {
    $("#"+box_id).effect("shake", {direction: "right", times: 2, distance: 8}, 350);
  }
  $("#feedback-"+box_id).animate({ opacity: 1 })
  $('#feedback-'+box_id).text(status);
  $("#feedback-"+box_id).delay(2000).animate({ opacity: 0 })
}

 $(document).on("click", "#save-button", function() {
   console.log("Applying edit");
   var skills = $("#skills :button").map(function() { return $(this).children().first().text();}).get();
   
   var formData = new FormData();
   formData.append('image', $("#upload").prop('files')[0]);

   formData.append("name", $("#name-field").val());

   formData.append("description", $("#description-field").val());

   formData.append("location", $("#location-field").val());

   formData.append("skills", JSON.stringify(skills));

    $.post({
      type: "POST",
      url: "/create/group/",
      data: formData,
      processData: false,
      contentType: false,
      success(response) {
        var response = JSON.parse(response);
        var status = response["status"];
        if (status === "Successfully saved") { location.replace("/profile/"); }
        else{message(status, response["box_id"], true);}
        
      }});
  });


function loadFile(input) {
  if (event.target.files[0]) {
  $("#image").attr('src', URL.createObjectURL(event.target.files[0]));
}
  console.log("WOOOOOW");
};

$(document).on("click", "#upload-button", function() {
  $("#upload").click();
});


$("#members-field").on('input', function() {
    if ($("#members-field").text().length > 0) {
    $.post({
      type: "POST",
      url: "/get/connections/",
      data: {"text":$("#members-field").text()},
      success(response) {
        var response = JSON.parse(response);
        var connections = response["connections"];
        $('#select-connections').empty();
        connections.forEach( function (profile, index) {
         $("#select-connections").append('<div valign="top" class="profile row media-bigBox" data-username="'+profile.username+'"><div class="media-column media-leftBox" ><img class="image" src="' + profile.profile_pic + '"></div><div class="media-column media-middleBox"><h1 style="color:black"><b>'+ profile.name +'</b></h1>');
        });
        $('#select-connections').removeClass("vanish");
      }
  });
  }
  else {
    $('#select-connections').addClass("vanish");
    $('#select-connections').empty();

  }
});

$(document).on("click", ".profile", function() {
  var username=$(this).data('username');

});