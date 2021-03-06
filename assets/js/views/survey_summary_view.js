define([
  "text!templates/_status.tpl.html",
  "text!templates/_sent_messages.tpl.html"
], function(statusTpl, sentMsgsTpl) {
  var HOVER_TEXT = {
    negative: "Adherence calculation is based only on patients' responses to the prompts. Non-responses to prompts are not included in the denominator of this adherence calculation.",
    missing: "Patient did not respond to this query."
  };

  var SurveySummaryView = {
    initialize: function(options) {
      _.bindAll(this, "render", "_renderSentMessages", "_statusIndicator");
      options.calendar.on("periodChanged", this.render);
    },

    className: "tab-pane",

    render: function() {
      this.$el.html(this.template({
        surveyName: this.options.name,
        survey: this.survey,
        dates: this.options.calendar.dates("iso8601"),
        statusIndicator: this._statusIndicator
      }));
      this._renderSentMessages();
    },

    _renderSentMessages: function() {
      if (!this.survey) return;
      var surveyKey = this.survey.name,
          self = this;

      this.$("#sent-messages").html(this._sentMessagesTemplate({
        messageCounts: _.map(this.options.calendar.dates("iso8601"), function(date) {
          return self.model.messages.countByContextAndDate(surveyKey, date);
        })
      }));
    },

    _sentMessagesTemplate: _.template(sentMsgsTpl),

    _statusIndicator: function(question, date) {
      var responseStatus = this.collection.responseStatus(question, date);
      var elClass = { negative: "bad", missing: "na" }[responseStatus.status];

      return elClass ? _.template(statusTpl, { elClass: elClass, text: responseStatus.explain }) : "";
    }
  };

  return SurveySummaryView;
});
