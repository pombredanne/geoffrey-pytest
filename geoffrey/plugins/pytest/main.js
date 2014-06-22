$(function() {

   var WipTestModel = Backbone.Model.extend({
     message: function(data) {
         console.dir(data);
         this.set("filename", data.value.filename);
         this.set("success", data.value.success);
         this.set("differences", data.value.differences);
     }

   });

   var WipTestApp = Backbone.View.extend({
     el: "#row2",

     initialize: function() {
       var this_ = this;
       this.listenTo(this.model, "change", this.render);

       $.get("/plugins/pytest/wip-widget.html", function(template){
         this_.template = _.template(template);
       }).done(function() { this_.render() });

       window.app.subscribe(
           'pytest',
           {'project': project_id,
            'plugin': 'pytest',
            'key': 'wip_tests'},
           function(data) { this_.model.message(data) });

       loadCSS("/plugins/pytest/wip-widget.css");
     },
 
     render: function() { 
       this.$el.html(this.template({'state': this.model.toJSON()}));

       return this;
     } 

   });

   var App = new WipTestApp({model: new WipTestModel()});
});
