'use strict';

Backbone.View.prototype.close = function () {
  this.remove();
  this.unbind();
  if (this.onClose) {
    this.onClose();
  }
}

var Turbine = {
  baseURL: 'http://localhost:5000',
  init: function () {
    this.router = new Turbine.Router();

    Backbone.history.start();
  },
  changeView: function (view) {
    if (this.currentView) {
      this.currentView.close();
    }

    view.render();

    this.currentView = view;
    this.currentView.render();

    $('#content').html(this.currentView.el);
  }
};

Turbine.Router = Backbone.Router.extend({

  routes: {
    "history/:teamId/:serviceId": "history",
    "*actions": "stat",
  },

  stat: function (actions) {
    Turbine.changeView(new Turbine.LoadingView())

    var self = this;

    $.ajax({
      dataType: 'json',
      url: Turbine.baseURL + '/check-results',
      success: function (data) {
        var view = new Turbine.StatusView();
        view.attributes = data;
        view.on('selected', function (teamId, serviceId) {
          self.navigate('history/' + teamId + '/' + serviceId, {trigger: true});
        });
        Turbine.changeView(view);
      }
    });
  },

  history: function (teamId, serviceId) {
    Turbine.changeView(new Turbine.LoadingView())

    $.ajax({
      dataType: 'json',
      url: Turbine.baseURL + '/check-results/' + teamId + '/' + serviceId,
      success: function (data) {
        var view = new Turbine.HistoryView();
        view.attributes = data;
        Turbine.changeView(view);
      }
    });
  }

});

Turbine.LoadingView = Backbone.View.extend({
  template: JST['app/scripts/templates/loading.ejs'],
  render: function () {
    this.$el.html(this.template())
  }
});

function transformSince($el) {
  $el.find('.since').each(function () {
    var checkedAt = moment(this.innerHTML);

    this.title = checkedAt.format('MMMM Do YYYY, h:mm:ss a');
    this.innerHTML = checkedAt.fromNow();

    $(this).tooltip();
  });
}

Turbine.StatusView = Backbone.View.extend({
  template: JST['app/scripts/templates/status.ejs'],
  events: {
    'click .service': 'selected',
  },
  render: function () {
    this.$el.html(this.template(this.attributes));
    transformSince(this.$el);
  },
  selected: function (e) {
    e.preventDefault();
    var $element = $(e.currentTarget);

    var teamId = $element.data('team');
    var serviceId = $element.data('service');

    this.trigger('selected', teamId, serviceId);
  },
});

Turbine.HistoryView = Backbone.View.extend({
  template: JST['app/scripts/templates/history.ejs'],
  render: function () {
    this.$el.html(this.template(this.attributes));
    transformSince(this.$el);
  }
});

$(document).ready(function () {
    Turbine.init();
});
