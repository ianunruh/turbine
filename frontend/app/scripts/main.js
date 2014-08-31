/* global moment, Backbone, $ */
'use strict';

Backbone.View.prototype.close = function () {
  this.remove();
  this.unbind();
  if (this.onClose) {
    this.onClose();
  }
};

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
    'history/:teamId/:serviceId': 'history',
    '*actions': 'stat',
  },

  stat: function () {
    $('#loading').show();

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
        view.on('expired', function () {
          self.stat();
        });
        Turbine.changeView(view);
        $('#loading').hide();
      }
    });
  },

  history: function (teamId, serviceId) {
    $('#loading').show();

    var self = this;

    $.ajax({
      dataType: 'json',
      url: Turbine.baseURL + '/check-results/' + teamId + '/' + serviceId,
      success: function (data) {
        var view = new Turbine.HistoryView();
        view.attributes = data;
        view.on('expired', function () {
          self.history(teamId, serviceId);
        });
        Turbine.changeView(view);
        $('#loading').hide();
      }
    });
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

    var self = this;

    this.t = setTimeout(function() {
      self.trigger('expired');
    }, 5 * 1000);
  },
  selected: function (e) {
    e.preventDefault();
    var $element = $(e.currentTarget);

    var teamId = $element.data('team');
    var serviceId = $element.data('service');

    this.trigger('selected', teamId, serviceId);
  },
  onClose: function () {
    if (this.t) {
      clearTimeout(this.t);
    }
  }
});

Turbine.HistoryView = Backbone.View.extend({
  template: JST['app/scripts/templates/history.ejs'],
  render: function () {
    this.$el.html(this.template(this.attributes));
    transformSince(this.$el);

    var self = this;

    this.t = setTimeout(function() {
      self.trigger('expired');
    }, 5 * 1000);
  },
  onClose: function () {
    if (this.t) {
      clearTimeout(this.t);
    }
  }
});

$(document).ready(function () {
  Turbine.init();
});
