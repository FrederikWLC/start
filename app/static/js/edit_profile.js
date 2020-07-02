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
   console.log($("#day").val());
   var skills = $("#skills :button").map(function() { return $(this).children().first().text();}).get();
   
   var formData = new FormData();
   formData.append('image', $("#upload").prop('files')[0]);

   formData.append("name", $("#name-field").val());

   formData.append("bio", $("#bio-field").val());

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

   formData.append("gender", $("#gender").val());

   formData.append("skills", JSON.stringify(skills));

    $.post({
      type: "POST",
      url: "/settings/profile/",
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


$(document).on('change','#selected-skill',function(){
               if ($('#selected-skill').val() != 'Select skill') {
                $('#add-skill').prop("disabled", false);
               }       
             });



 $(document).on("click", "#add-a-skill", function() {
    $('#add-a-skill').addClass("vanish");
    $('#select-skill').removeClass("vanish");
    if ($('#selected-skill').val() == 'Select skill') {
            $('#add-skill').prop("disabled", true);
    }       
    $('#add-skill').removeClass("vanish");
  });

 $(document).on("click", "#add-skill", function() {
  $('#select-skill').addClass("vanish");
  $('#add-skill').addClass("vanish");
  $('#add-a-skill').removeClass("vanish");
  $("#skills").append("<div class='skill'><button class='button is-info is-normal is-'><span class='skill-title'>"+$('#selected-skill').val()+"</span><span class='icon remove-skill'><a class='delete'></a></span></button></div>");
  $('#selected-skill option:selected').remove();
  console.log($('#selected-skill').children().length)
  if ($('#selected-skill').children().length == 1) {
    $('#add-a-skill').addClass("vanish");
  }
 });


 $(document).on("click", ".remove-skill", function() {
  $('#selected-skill').append('<option>'+$(this).prev('span').text()+'</option>')
  $(this).closest('div').remove();
  $('#add-a-skill').removeClass("vanish");

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
