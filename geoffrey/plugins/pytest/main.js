$(function() {

   var WipTestModel = Backbone.Model.extend({

     url: '/api/v1/' + project_id + '/pytest/state',

     message: function(data) {
         this.set("filename", data.value.filename);
         this.set("success", data.value.success);
         this.set("differences", data.value.differences);
         this.set("status", data.value.status);
         this.set("details", data.value.details);
     },

     parse: function(response, options) {
       if(response && response.length > 0){
         this.set("filename", response[0].value.filename);
         this.set("success", response[0].value.success);
         this.set("differences", response[0].value.differences);
         this.set("status", response[0].value.status);
         this.set("details", response[0].value.details);
       }

     }

   });

   var WipTestApp = Backbone.View.extend({

     initialize: function() {
       var this_ = this;

       $.get("/plugins/pytest/wip-widget.html", function(template){
         this_.template = _.template(template);
       }).done(function() { 
         this_.model.fetch().done(function() {
           this_.render();
           window.app.registerWidget(this_);
         });
       });

       window.app.subscribe(
           'pytest_wip',
           {'project': project_id,
            'plugin': 'pytest',
            'key': 'wip_tests'},
           function(data) {
               this_.model.message(data);
               this_.render();
           });

       window.app.subscribe(
           'pytest_wip_status',
           {'project': project_id,
            'plugin': 'pytest',
            'type': 'custom',
            'key': 'wip_tests_status'},
           function(data) { this_.toggleStatus(data.value.status) });
       loadCSS("/plugins/pytest/wip-widget.css");
     },

     render: function() {
       this.$el.attr("data-ss-colspan", "3");

       var state = this.model.toJSON();
       var btnColor = "";
       var btnText = "";
       switch (state.status) {
         case "passed":
           btnColor = "btn-success";
           btnText = "passed";
           break;
         case "failed":
           btnColor = "btn-danger";
           btnText = "failed";
           break;
         default:
           btnColor = "";
           btnText = "unknown";
           break;
       }

       this.toggleStatus(state.status);
       this.$el.html(this.template({
         'state': state,
         'btnColor': btnColor,
         'btnText': btnText}));

       this.ladda = undefined;

       return this;
     },

     toggleStatus: function(status) { 
         var button = $("#wip-status");
         if (button[0]) {
             if (!this.ladda) {
               this.ladda = Ladda.create(button[0]);
             }

             $("#wip-status-message").html(status);

             button.removeClass("btn-success");
             button.removeClass("btn-danger");
             button.removeClass("btn-warning");
             switch (status) {
               case "running":
                 button.addClass("btn-warning");
                 this.ladda.start();
                 break;
               case "passed":
                 button.addClass("btn-success");
                 this.ladda.stop();
                 break;
               case "failed":
                 button.addClass("btn-danger");
                 this.ladda.stop();
                 break;
               case "errored":
                 btnColor = ""
                 this.ladda.stop();
                 break;
             }
         }
     }

   });

   var App = new WipTestApp({model: new WipTestModel()});
});
