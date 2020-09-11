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
   save();
  });

function save() {
  var formData = new FormData();
   formData.append('image', $("#upload").prop('files')[0]);

   formData.append("handle", $("#handle-field").val());

   formData.append("name", $("#name-field").val());

   formData.append("description", $("#description-field").val());

   formData.append("privacy", $("#privacy-field").val());

   formData.append("location_is_fixed", $("#location-status-field").val());

   if ($("#location-status-field").val() == 1) {
   formData.append("address", $("#location-field").val());
 }

   formData.append("members", JSON.stringify($("#member-tags-container").children().toArray().map( element => $(element).data('username'))));

    $.post({
      type: "POST",
      url: "/create/group/",
      data: formData,
      processData: false,
      contentType: false,
      success(response) {
        var response = JSON.parse(response);
        var status = response["status"];
        if (status === "Successfully saved") { location.replace("/connections/"); }
        else{message(status, response["box_id"], true);}
        
      }});
}

function updatePlaceholder() {
  console.log($("#member-tags-container").children().length);
  if ($("#member-tags-container").children().length == 0) {
    $("#members-text-field").addClass('placeholder');
}
  else {
    $("#members-text-field").removeClass('placeholder');
  }
}

function loadFile(input) {
  if (event.target.files[0]) {
  $("#image").attr('src', URL.createObjectURL(event.target.files[0]));
}

}

$(document).on("click", "#upload-button", function() {
  $("#upload").click();
});


function get_connections_from_text() {
  var text = $("#members-text-field").text();
  var already_chosen = $("#member-tags-container").children().toArray().map( element => $(element).data('username'));
  if (text.length > 0) {
    var formData = new FormData();
    formData.append('text', text);
    formData.append('already_chosen', JSON.stringify(already_chosen));
    $.post({
      type: "POST",
      url: "/get/connections/",
      data: formData,
      processData: false,
      contentType: false,
      success(response) {
        var response = JSON.parse(response);
        var connections = response["connections"];
        $('#select-connections').empty();
        connections.forEach( function (profile, index) {
         $("#select-connections").append('<div valign="top" class="row profile-bigBox" data-username="'+profile.username+'" data-name="'+profile.name+'"><div class="profile-column profile-leftBox" ><img class="image" src="' + profile.profile_pic + '"></div><div class="profile-column profile-rightBox"><h1><b>'+ profile.name +'</b></h1>');
        });
        if (!$('#select-connections').is(':empty')){
        $('#select-connections').removeClass("vanish");
        updateScroll();
      }
      else {
        $('#select-connections').addClass("vanish");
      }

      }
  });}
  else {
    $('#select-connections').addClass("vanish");
    $('#select-connections').empty();

  }
}

$("#members-text-field").on('input', function() {
    get_connections_from_text();
});

$(document).on("click", "#members-field", function() {
  $("#members-text-field").focus();
});

function updateScroll(){
    var element = document.getElementById("container");
    element.scrollTop = element.scrollHeight;
}

function add_member(name, username) {
  $("#members-text-field").focus();
  $("#members-text-field").text("");
  $("#member-tags-container").append('<div class="profile tag is-medium" data-username="'+username+'"><span>'+name+'</span><span class="icon remove-member"><a class="delete"></a></span></div>')
  updatePlaceholder();
  get_connections_from_text();
}

$(document).on("click", function(e) {
  if (!($(e.target)[0] === $("#members-field")[0] || $(e.target).parent()[0] === $("#members-field")[0])) {
  $('#select-connections').addClass("vanish");
  $('#select-connections').empty();
}
});

$(document).on("click", "#members-field", function() {
  get_connections_from_text();
});

$(document).on("click", ".profile-bigBox", function() {
  add_member(name=$(this).data('name'),username=$(this).data('username'));
});



$(document).on("click", ".remove-member", function() {
  $(this).closest('div').remove();
  updatePlaceholder();
});

$(document).on('change', '#location-status-field', function() {
  if ($('#location-status-field').val() == 0) {
    $('#location-field').addClass("vanish");
  }
  else {
    $('#location-field').removeClass("vanish");
  }
  });

$(document).on('keydown', '#members-text-field', function(event) {
    var key = event.keyCode || event.charCode;

    if (key == 8 && $("#members-text-field").text().length == 0){
        $("#member-tags-container").children().last().remove();
      }

    if (key == 13 || key == 9 || key == 10) {
      if (key == 10 || key == 13) {
        event.preventDefault();
      }
      if ($(".hovered").length == 1) {
      add_member(name=$(".hovered").data('name'),username=$(".hovered").data('username'));
    }
    }
  });


$(document).on('mouseover', '.profile-bigBox', function() {
  $(this).addClass('hovered');
});

$(document).on('mouseleave', '.profile-bigBox', function() {
  $(this).removeClass('hovered');
});