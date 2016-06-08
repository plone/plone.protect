$.ajax({
  type: 'POST',
  url: '/@@sample',
  data: {
    value: Math.random(),
  },
  success: function(msg) {
    console.log('success ' + msg);
  },
  error: function(msg) {
    console.log('error ' + msg);
  }

});
