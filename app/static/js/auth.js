
function message(status, box_ids, shake=false) {
  $("#feedback").stop(stopAll=true);
  box_ids.forEach( function (box_id, index) {
    if (shake) {
    $("#"+box_id).effect("shake", {direction: "right", times: 2, distance: 8}, 350);
  }
  $("#feedback").animate({ opacity: 1, queue: false })
});
  $('#feedback').text(status);
  $("#feedback").delay(2000).animate({ opacity: 0, queue: false });
}
  
 $(document).on("click", "#register-button", function() {
   console.log("REGISTER");
   var formData = new FormData();

   formData.append("name", $("#name-field").val());

   formData.append("location", $("#location-field").val());

   if ($("#month").val()) {
   formData.append("month", $("#month").val());
   }
   
   if ($("#day").val()) {
   formData.append("day", $("#day").val());
   }

   if ($("#year").val()) {
   formData.append("year", $("#year").val());
    }

  formData.append("username", $("#username-field").val());
  
  formData.append("email", $("#email-field").val());

  formData.append("password", $("#password-field").val());

    $.post({
      type: "POST",
      url: "/register/",
      data: formData,
      processData: false,
      contentType: false,
      success(response) {
        var response = JSON.parse(response);
        var status = response["status"];
        if (status === "Successfully registered") { location.reload(); }
        else{message(status, response["box_ids"], true);}

        
      }});
  });

    $(document).on("click", "#login-button", function() {
      console.log("LOGIN");
    $.post({
      type: "POST",
      url: "/login/",
      data: {"username": $("#login-username").val(), 
             "password": $("#login-pass").val()},
      success(response) {
          var response = JSON.parse(response);
          var status = response["status"];
          if (status === "Successfully logged in") { location.reload(); }
          else{console.log(response["box_ids"]);
            message(status, response["box_ids"], true);}
          

    }});
  });