// Kept after the app was retired (#270, #288): nothing on the site loads this file. The explorer's
// old-link test (viz/explorer/test/unit/agency-legacy.test.js) runs convertToSlug from it, so old
// /agencies/ links are checked against the real slug rule.
var BudgetHelpers = BudgetHelpers || {};
var BudgetHelpers = {

  //converts a text in to a URL slug
  convertToSlug: function(text) {
    if (text == undefined) return '';
  	return text
        .toLowerCase()
        .replace(/[^\w ]+/g,'')
        .replace(/ +/g, '-');
  },

  // Builds a cache of templates that get fetched and rendered by views
  template_cache: function(tmpl_name, tmpl_data){
      if ( !BudgetHelpers.template_cache.tmpl_cache ) {
          BudgetHelpers.template_cache.tmpl_cache = {};
      }

      if ( ! BudgetHelpers.template_cache.tmpl_cache[tmpl_name] ) {
          var tmpl_dir = 'js/views';
          var tmpl_url = tmpl_dir + '/' + tmpl_name + '.html?4';

          var tmpl_string;
          $.ajax({
              url: tmpl_url,
              method: 'GET',
              async: false,
              success: function(data) {
                  tmpl_string = data;
              }
          });

          BudgetHelpers.template_cache.tmpl_cache[tmpl_name] = _.template(tmpl_string);
      }

      return BudgetHelpers.template_cache.tmpl_cache[tmpl_name](tmpl_data);
  },

  // Money for display. A year with no published figure (an empty CSV cell, which sums to
  // NaN) shows as "Not yet published" rather than "$0.00". Used for the newest year's
  // Modified budget, which the City publishes only after the next year is adopted.
  formatMoney: function(value){
      if (value === null || typeof value === 'undefined' || isNaN(value)){
          return 'Not yet published';
      }
      return accounting.formatMoney(value);
  },

  calc_change: function(cur, prev){
      if (isNaN(cur) || isNaN(prev)){
          return null
      }
      if (prev == 0){
          return null
      }
      if (cur == 0 && prev == 0){
          return null
      }
      var change = parseFloat(((cur - prev) / prev) * 100);
      if (change < 0){
          change = change.toFixed(1) + '%';
      } else {
          change = '+' + change.toFixed(1) + '%';
      }
      return change
  }
}
