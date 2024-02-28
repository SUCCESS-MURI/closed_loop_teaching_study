/*
 * Example plugin template
 */

var path = null;
var mdp_parameters = null;
var primary_misc = {};
var stim = null;
var source = null;

jsPsych.plugins["sim-instructions2"] = (function() {
  jsPsych.pluginAPI.registerPreload('video-keyboard-response', 'stimulus', 'video');

  var plugin = {};

  plugin.info = {
    name: "sim-instructions2",
    description: '',
    parameters: {
      pages: {
        type: jsPsych.plugins.parameterType.HTML_STRING,
        pretty_name: 'Pages',
        default: undefined,
        array: true,
        description: 'Each element of the array is the content for a single page.'
      },

      
      stimulus: {
        type: jsPsych.plugins.parameterType.HTML_STRING,
        pretty_name: 'Stimulus',
        default: null,
        description: 'The HTML string to be displayed'
      },
      iframe_id: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'iFrame ID',
        default: null,
        description: 'The id of an iFrame (if applicable) to allow access to variables'
      },
      iframe_src: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'iFrame src',
        default: null,
        description: 'The path to any content to be loaded into the iFrame'
      },
      preamble: {
        type: jsPsych.plugins.parameterType.HTML_STRING,
        pretty_name: 'Preamble',
        default: null,
        description: 'String to display at top of the page.'
      },
      legend: {
        type: jsPsych.plugins.parameterType.HTML_STRING,
        pretty_name: 'Legend',
        default: null,
        description: 'String to display at bottom of the page.'
      },
      
      caption: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Caption',
        default: null,
        description: 'Caption for Images in Domain 1, Rating Tasks'
      },
      
      scale_width: {
        type: jsPsych.plugins.parameterType.INT,
        pretty_name: 'Scale width',
        default: null,
        description: 'Width of the likert scales in pixels.'
      },
      button_label: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Button label',
        default:  'Continue',
        description: 'Label of the button.'
      },
      condition: {
        type: jsPsych.plugins.parameterType.INT,
        pretty_name: 'Condition',
        default: null,
        description: 'Identifies which condition the participant was assigned to.'
      },
      domain: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Domain',
        default: null,
        description: 'Identifies which domain the primary question was in.'
      },
      textinput: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Text input',
        default: null,
        description: 'Placeholder for textbox'
      },
      question_type: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'QuestionType',
        default: null,
        description: 'Identifies what type of question is being asked.'
      },
      counterbalance: {
        type: jsPsych.plugins.parameterType.INT,
        pretty_name: 'Counterbalance',
        default: null,
        description: 'Identifies which counterbalancing the participant was assigned to.'
      },
      train_test_set: {
        type: jsPsych.plugins.parameterType.INT,
        pretty_name: 'Train test set',
        default: null,
        description: 'Identifies which train/test set the participant was assigned to.'
      },
      continue_condition: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Continue condition',
        default: null,
        description: 'Requirements needed to continue on.'
      },
      randomize_question_order: {
        type: jsPsych.plugins.parameterType.BOOL,
        pretty_name: 'Randomize question order',
        default: null,
        description: 'Randomize question order.'
      },
      /*mdp_parameters: {
        type: jsPsych.plugins.parameterType.OBJECT,
        pretty_name: 'MDP parameters',
        default: {},
        description: 'MDP parameters of the testing simulation.'
      },*/

      key_forward: {
        type: jsPsych.plugins.parameterType.KEYCODE,
        pretty_name: 'Key forward',
        default: 'rightarrow',
        description: 'The key the subject can press in order to advance to the next page.'
      },
      key_backward: {
        type: jsPsych.plugins.parameterType.KEYCODE,
        pretty_name: 'Key backward',
        default: 'leftarrow',
        description: 'The key that the subject can press to return to the previous page.'
      },
      allow_backward: {
        type: jsPsych.plugins.parameterType.BOOL,
        pretty_name: 'Allow backward',
        default: true,
        description: 'If true, the subject can return to the previous page of the instructions.'
      },
      allow_keys: {
        type: jsPsych.plugins.parameterType.BOOL,
        pretty_name: 'Allow keys',
        default: true,
        description: 'If true, the subject can use keyboard keys to navigate the pages.'
      },
      show_clickable_nav: {
        type: jsPsych.plugins.parameterType.BOOL,
        pretty_name: 'Show clickable nav',
        default: false,
        description: 'If true, then a "Previous" and "Next" button will be displayed beneath the instructions.'
      },
      show_page_number: {
          type: jsPsych.plugins.parameterType.BOOL,
          pretty_name: 'Show page number',
          default: true,
          description: 'If true, and clickable navigation is enabled, then Page x/y will be shown between the nav buttons.'
      },
      button_label_previous: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Button label previous',
        default: 'Previous',
        description: 'The text that appears on the button to go backwards.'
      },
      button_label_next: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Button label next',
        default: 'Next',
        description: 'The text that appears on the button to go forwards.'
      }
    }
  }

  plugin.trial = function(display_element, trial) {
    continue_condition = trial.continue_condition;
    if (trial.iframe_src != null) {
      path = trial.iframe_src
    }
    primary_misc = {};
    
    window.current_page = 0;

    var view_history = [];

    window.watched_vid_arr = new Array(trial.pages.length).fill(false);
    video_lengths_arr = new Array(trial.pages.length).fill(0.0);


    var video_loops_arr = new Array();
    var video_curr_times_arr = new Array();

    for(var i=0; i < trial.pages.length; i++) {
      video_loops_arr.push([]);
      video_curr_times_arr.push([]);
    }

    var start_time = performance.now();

    var last_page_update_time = start_time;

    function btnListener(evt){
    	evt.target.removeEventListener('click', btnListener);
    	if(this.id === "jspsych-instructions-back"){
    		back();
    	}
    	else if(this.id === 'jspsych-instructions-next'){
    		next();
    	}
    }

    function show_current_page() {
      source = trial.pages[current_page][0];
    mdp_parameters = trial.pages[current_page][1];
    if (trial.domain == 'augmented_taxi2') {
      stim = '<iframe id = "ifrm" style="border:none;" src="' + source + '" height="550" width="750" title="Iframe Example"></iframe>  '
      //mdp_parameters =  mdp_parameters.augmented_taxi2
  } else if (trial.domain == 'colored_tiles') {
      stim = '<iframe id = "ifrm" style="border:none;" src="' + source + '" height="700" width="700" title="Iframe Example"></iframe>    '
      //mdp_parameters =  mdp_parameters.colored_tiles
  }
  else {
      stim = '<iframe id = "ifrm" style="border:none;" src="' + source + '" height="600" width="800" title="Iframe Example"></iframe>    '
      //mdp_parameters =  mdp_parameters.skateboard2
  }
      
      var html = '';
      html += '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">';
      html += '<link rel=\"stylesheet\" href=\"/static/css/style.css\" type=\"text/css\"/>';

      html += '<div>';


    /* START PRIMARY QUESTION */
    // show preamble text
    if(trial.preamble !== null){
      html += '<div id="jspsych-html-button-response-preamble" class="jspsych-html-button-response-preamble">'+trial.preamble+'</div>';
    }



      // display stimulus
      if (trial.legend != null) {
          html += '<div class="row"><div class="column">';
          html += '<div id="jspsych-html-button-response-stimulus">' + stim + '</div>';
          if (trial.caption !== null) {
              html += '<p>' + trial.caption + '</p>'
          }
          html += '</div>';
          html += '<div class="column">';

          if (trial.legend !== null) {
              html += '<div id="jspsych-html-button-response-legend" class="jspsych-html-button-response-legend">' + trial.legend + '</div>';
          }
          html += '</div></div>';
      }
      else {
          html += '<div id="jspsych-html-button-response-stimulus">'+stim +'</div>';
          if (trial.caption !== null){
      html += '<p>' + trial.caption + '</p>'
          }
      }





      var pagenum_display = "";
      if(trial.show_page_number) {
          pagenum_display = "<span style='margin: 0 1em;' class='"+
          "jspsych-instructions-pagenum'>Page "+(current_page+1)+"/"+trial.pages.length+"</span>";
      }



    

      if (trial.show_clickable_nav) {

        var nav_html = "<div class='jspsych-instructions-nav' style='padding: 10px 0px;'>";
        if (trial.allow_backward) {
          var allowed = (current_page > 0 )? '' : "disabled='disabled'";
          nav_html += "<button id='jspsych-instructions-back' class='jspsych-btn' style='margin-right: 5px;' "+allowed+">&lt; "+trial.button_label_previous+"</button>";
        }
        if (trial.pages.length > 1 && trial.show_page_number) {
            nav_html += pagenum_display;
        }

        if (watched_vid_arr[current_page] == false) {
          nav_html += "<button id='jspsych-instructions-next' class='jspsych-btn'"+
              "style='margin-left: 5px;' "+"disabled='disabled'"+ ">"+trial.button_label_next+
              " &gt;</button></div>";
        } else {
          nav_html += "<button id='jspsych-instructions-next' class='jspsych-btn'"+
              "style='margin-left: 5px;'>"+trial.button_label_next+
              " &gt;</button></div>";
        }

        html += nav_html;
        display_element.innerHTML = html;
        if (current_page != 0 && trial.allow_backward) {
          display_element.querySelector('#jspsych-instructions-back').addEventListener('click', btnListener);
        }

        display_element.querySelector('#jspsych-instructions-next').addEventListener('click', btnListener);
      } else {
        if (trial.show_page_number && trial.pages.length > 1) {
          // page numbers for non-mouse navigation
          html += "<div class='jspsych-instructions-pagenum'>"+pagenum_display+"</div>"
        }
        display_element.innerHTML = html;
      }

      function checkFlag() {
        if(watched_vid_arr[current_page] == false) {
             window.setTimeout(checkFlag, 100); /* this checks the flag every 100 milliseconds*/
          } else {
            if ($('#jspsych-instructions-next').is(':disabled')) {
              $('#jspsych-instructions-next').removeAttr('disabled');
            }
          }
      }
      checkFlag();

    }

    function next() {

      add_current_page_to_view_history()

     
      current_page++;

      // if done, finish up...
      if (current_page >= trial.pages.length) {
        endTrial();
      } else {
        show_current_page();
      }

    }

    function back() {

      add_current_page_to_view_history()

      // if the video length hasn't been initialized yet, initialize it
      
      current_page--;

      show_current_page();
    }

    function add_current_page_to_view_history() {

      var current_time = performance.now();

      var page_view_time = current_time - last_page_update_time;

      view_history.push({
        page_index: current_page,
        viewing_time: page_view_time
      });

      last_page_update_time = current_time;
    }

    function endTrial() {
      display_element.innerHTML = '';

      var trial_data = {
        // Primary information
        "primary_stimulus": JSON.stringify(view_history),
        "primary_rt": performance.now() - start_time,
        "primary_answer": {"video_lengths": video_lengths_arr,
          "video_loops": video_loops_arr,
          "video_curr_times": video_curr_times_arr},

        // Testing information
        "test_mdp": mdp_parameters,

        // Likert information
        "likert_rt": null,
        "likert_response": null,
        "likert_question_order": null,

        // Study information
        "domain": trial.domain,
        "condition": trial.condition,
        "counterbalance": trial.counterbalance,
        "train_test_set": trial.train_test_set,
        "question_type": trial.question_type
      };
      jsPsych.finishTrial(trial_data);
    }

    function set_rt_and_enable_submit() {
      if(trial.iframe_id !== null) {
          if (document.getElementById(trial.iframe_id).contentWindow['final_data'].length > 0) {
              if ($('#jspsych-survey-likert-next').is(':disabled')) {
                  $('#jspsych-survey-likert-next').removeAttr('disabled');
                  primaryEndTime = performance.now();
                  console.log("primaryEndTime recorded");
                  var primary_rt = primaryEndTime - primaryStartTime;
                  primary_response.primary_rt = primary_rt;
              }
          }
      } else {
          if (trial.question_type == 'training_video' && watched_video == false) {
              return
          } else {
              $('#jspsych-survey-likert-next').removeAttr('disabled');
          }
      }
  }

    if (trial.iframe_id != null) {
      var iframe = document.getElementById(trial.iframe_id)
      $(iframe).load(function(){

          $(this).contents().find("body").on('mouseup', function(e) {
              set_rt_and_enable_submit()
          });

          $(this).contents().find("body").on('mousedown', function(e) {
              set_rt_and_enable_submit()
          });

          iframe.contentWindow.document.addEventListener("game-completed", function(e) {
              set_rt_and_enable_submit()
          });

          // no need for participant to do anything in order to continue
          if (trial.domain == 'sandbox' && trial.continue_condition == 'free_play') {
              $('#jspsych-survey-likert-next').removeAttr('disabled');
          }
      });
      var curr_ifrm = false
    }

    show_current_page();

  };

  return plugin;

})();
