var timeout;

function $(id) {
    return document.getElementById(id);
};

var bins = document.getElementsByClassName("bin");
dragArr = [$("staging")]
for (i = 0; i < bins.length; i++) {
    dragArr[i + 1] = $(bins[i].id);
}
var drake = dragula(dragArr, {
    invalid: function(el, handle) {
        if (el.classList.contains('prev-card')) {
            return (true);
        } else {
            return (false);
        };
    },
}).on("drop", function(el, target, source) {
    var chosen_bin = document.getElementById("current-chosen-bin");
    chosen_bin.textContent = el.parentElement.id;
    console.log("Moved to " + el.parentElement.id);
    var cur_switches = document.getElementById("switches");
    var new_num;
    if (target.id != source.id) {

        //Update switches
        if (cur_switches.value.length == 0) {
            cur_switches.value = 1;
        } else {
            new_num = String(parseInt(cur_switches.value) + 1);
            cur_switches.value = new_num;
        }
        console.log("Switches " + cur_switches.value);
    }
});

function showFeedback() {
    var submit_choice_btn = document.getElementById("submit_choice_btn");
    var chosen_bin = document.getElementById("current-chosen-bin").textContent;
    var video_obj = document.getElementById("robot-video");
    var correct_bin = document.getElementById("correct_bin").textContent;
    var correct_vid_name = document.getElementById("correct_vid_name").textContent;
    var incorrect_vid_name = document.getElementById("incorrect_vid_name").textContent;
    console.log("Chose " + chosen_bin);
    if (chosen_bin == "staging" || chosen_bin == "") {
        alert("Please choose one of the two bins!")
    } else {
        submit_choice_btn.classList.add("invisible");
        drake.destroy();

        var video_name;
        if (correct_bin == chosen_bin) {
            video_name = correct_vid_name; //Replace this when we have all the videos
        } else {
            video_name = incorrect_vid_name;
        }

        var feedback_chosen_obj = document.getElementById("feedback_chosen");
        feedback_chosen_obj.value = video_name;

        video_obj.innerHTML = '<source id="robot-video-source" src="' + '../static/robot/' + video_name + '.mp4' + '" type="video/mp4">';
        video_obj.addEventListener('ended', videoEnded, false);
        video_obj.loop = false
        video_obj.load();
        video_obj.play();
    }
}

function videoEnded(e) {
    // What you want to do after the event
    var chosen_bin_obj = document.getElementById("chosen_bin");
    chosen_bin_obj.value = document.getElementById('current-chosen-bin').textContent;
    var submit_trial_btn = document.getElementById("submit_trial");
    submit_trial_btn.click();
}