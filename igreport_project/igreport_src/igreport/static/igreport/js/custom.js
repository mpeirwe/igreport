//
function jqpopup(title, btns, w, h) {
	buttons = {};

	if (btns) {
		for(var i=0; i<btns.length; i++) {
			buttons['b'+i] = {text:btns[i].text, click:btns[i].click};
		}
	}

	buttons['Cancel'] = function() { $(this).dialog('destroy'); };

        try {
                var d = $('#jqpopup').dialog({
                        autoOpen: false,
			modal: true,
			minHeight: h,
			minWidth: w,
			title: title,
			closeOnEscape: false,
                        buttons: buttons,
                 });
                d.dialog('open');
		d.dialog('option', 'position', "center");

        } catch(a) {alert(a);}
	
	return false;
};

function editrpt(rid) {
	
	ajax_wait('Getting Report Information ..');
//
	var url = '/igreports/' + rid + '/getreport/';
	var r = createHttpRequest();
	r.open('GET', url, true);
	
	r.onreadystatechange = function() {
		if(r.readyState == 4) {
			ajax_done();
			if(r.status != 200) {
				alert(r.responseText);
				return;
			}
			if(/{error:false/.test(r.responseText)) {
				var o = eval('('+ r.responseText +')');
				var rpt = o.res.rpt;
				var dist = o.res.dist;
				//var scty = o.res.scty;
				var cat = o.res.cat;
				var comm = o.res.comm;
				var curr = o.res.curr;
				
				var doptions = '';
				for(var i=0; i<dist.length; i++) {
					doptions += '<option value="'+dist[i].id+'"'+(dist[i].id==rpt.district_id?' selected="selected"':'')+'>'+dist[i].name+'</option>';
				}
				var coptions = '';
				for(var i=0; i<curr.length; i++) {
					coptions += '<option value="'+curr[i].id+'"'+(curr[i].id==rpt.currency_id?' selected="selected"':'')+'>'+curr[i].code+'</option>';
				}				
				var cathtml = '';
				if(cat.length) {
					for(var i=0; i<cat.length; i++) {
						cathtml += '<div style="padding-bottom:3px"><input type="checkbox" id="cat_'+cat[i].id+'" name="category" value="'+cat[i].id+'"'+(cat[i].checked?' checked="checked"':'')+'/>&nbsp;<label class="rpt-option-label" for="cat_'+cat[i].id+'">'+cat[i].name+'</label></div>';
					}
				}
				if(!cathtml) {
					cathtml = '<h3>[No Report Categories Configured]</h3>';
				} else {
					cathtml = '<div style="border:solid #ccc 1px;height:70px;overflow:auto;padding:10px">'+cathtml+'</div>';
				}
				var comments = '';
				if(comm.length>0) {
					for(var i=0; i<comm.length; i++) {
						comments += '<div style="padding-top:7px">#'+(i+1)+'.&nbsp;'+comm[i].comment+' by <strong>'+comm[i].user+
						'</strong> on <strong>'+comm[i].date+'</strong></div>';
					}
					comments = '<div style="padding-top:5px"><strong>Current Comments</strong>:<br/>'+comments+'</div>';
				}
				var html = '<div class="report"><form id="rptform"><table border="0" cellpadding="0" cellspacing="0"><tr><td colspan="2"><div class="rpt-title">Submitted by <span style="color:#ff6600;font-weight:bold">'+rpt.sender+'</span> on <span style="color:#ff6600;font-weight:bold">'+rpt.date+'</span></div></td></tr><tr><td><div class="rpt-label">Report</div><div><textarea id="report" name="report" class="rpt-ta" readonly="readonly">'+rpt.report+'</textarea></div></td><td><div class="rpt-label">Accused</div><div><textarea id="subject" name="subject" class="rpt-ta">'+rpt.accused+'</textarea></div></td></tr><tr><td><div class="rpt-label">District</div><div><select id="dist" name="district" class="rpt-list">'+doptions+'</select><br/>(User reported: <span style="color:#CC0000">'+rpt.district_ff+'</span>)</div></td><td><div class="rpt-label">Amount</div><div><select id="currency" name="currency" class="rpt-list">'+coptions+'</select>&nbsp;<input type="text" id="amount" name="amount" onkeydown="damt(this)" onkeyup="damt(this)" value="'+rpt.amount+'" /><br/>(User reported: <span style="color:#CC0000">'+rpt.amount_ff+'</span>)</div></td></tr><tr><td><div class="rpt-label">Name of Reporter</div><div><textarea id="names" name="names" class="rpt-ta">'+rpt.names+'</textarea></div></td><td><div class="rpt-label">Case Category</div><div>'+cathtml+'</div></td></tr><tr><td><div class="rpt-label">Comments</div><div><textarea id="comments" name="comments" class="rpt-ta"></textarea><input type="hidden" name="id" value="'+rid+'" /><input type="hidden" name="csrfmiddlewaretoken" value="'+getCookie('csrftoken')+'" /></div><div style="padding-top:15px"><input type="checkbox" name="closed" value="close" id="closecb" />&nbsp;<label for="closecb"><span style="color:#ff0000">CLOSE REPORT</span></label></div><div>This report can not be modified once it is closed</div></td><td>'+comments+'</td></tr></table></form></div>';
				
				var title = 'User Report Details';
				var btns = [{text:'Submit', click:function(){ update_rpt(rid); }}]
				
				document.getElementById('jqpopup').innerHTML = html;
				jqpopup(title, btns, 850, 450);
				
				//$.datepicker.setDefaults({ dateFormat: 'mm/dd/yy' });
				//$("#date").datepicker();
				damt(document.getElementById('amount'));
			}
		}
	}
	r.send(null);	
};

function damt(input) {
	var nStr = input.value + '';
	nStr = nStr.replace( /\,/g, "");
	var x = nStr.split( '.' );
	var x1 = x[0];
	var x2 = x.length > 1 ? '.' + x[1] : '';
	var rgx = /(\d+)(\d{3})/;
	while ( rgx.test(x1) ) {
		x1 = x1.replace( rgx, '$1' + ',' + '$2' );
	}
	input.value = x1 + x2;
};

function update_rpt(rid) {

	var params = $('#rptform').serialize();
	ajax_wait('Updating Report. Please wait ..');
        var r = createHttpRequest();
	
        r.open('POST', '/igreports/' + rid + '/', true);
        r.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
	
        r.onreadystatechange = function(){
                if(r.readyState == 4){
			ajax_done();
			if(r.status != 200) {
				//alert(r.statusText);
				alert(r.responseText);
				return;
			}
			// success reload page
			$('#jqpopup').dialog('close');
			ajax_wait_update('Report updated. Refreshing ..')
			window.location.replace(window.location);
		}
	}
	r.send(params);
	
	return true;	
};

function syncit(rpt) {
	//if(!confirm('Sync Report?')) {
	//	return;
	//}
	if(rpt.amount.length == 0 && rpt.amountff.length>0) {
		if(/^[0-9]+/i.test(rpt.amountff)) {
			if(!confirm('Amount appears not to be set yet the user submitted "'+
				rpt.amountff+'". Proceed?')) {
				return false;
			}
		}
	}
	ajax_wait('Syncing Report. Please wait ..');
	
	var r = createHttpRequest();
        r.open('POST', '/igreports/' + rpt.id + '/sync/', true);
        r.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
		
	r.onreadystatechange = function() {
		if(r.readyState == 4) {
			ajax_done();
			if(r.status != 200) {
				alert(r.responseText);
				return;
			}
			alert('Report Successfuly synced');
			window.location.replace(window.location);
		}
	}
	r.send('csrfmiddlewaretoken='+getCookie('csrftoken'));
}

function smsp(id, msisdn, src) {
	
	var title = 'Send SMS to ' + msisdn;
	var btns = [{text:'Send SMS', click:function(){ send_(); }}]
	var txt = document.getElementById('rpt_' + id).innerHTML;
	
	var html = '<form id="msgf"><div style="padding:30px 0px 0px 30px">\
	    <div class="rpt-label">User Report</div><div style="padding-bottom:20px">' + txt + '</div>\
	    <div class="rpt-label">SMS Message</div><div><textarea name="message" rows="5" cols="50" class="rpt-ta-general" onkeydown="track_msg_len(this)" onkeyup="track_msg_len(this)"></textarea><br/>\
	    <input type="text" size="10" id="id_chars" readonly="readonly" value="0 Chars" style="color:#666" />\
	    <input type="hidden" name="src" value="'+src+'" /><input type="hidden" name="id" value="'+id+'" /><input type="hidden" name="msisdn" value="'+msisdn+'" />\
	    </div>\
	</div></form>';				
	document.getElementById('jqpopup').innerHTML = html;
	jqpopup(title, btns, 600, 300);	
};

function send_() {
	var f = document.getElementById('msgf');
	if(f.message.value.length < 2) {
		alert('Specify a valid message to send');
		return;
	}
	ajax_wait('Sending SMS to ' + f.msisdn.value + '. Please wait ..');
	
	var r = createHttpRequest();
        r.open('POST', '/igreports/' + f.id.value + '/sms/', true);
        r.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
		
	r.onreadystatechange = function() {
		if(r.readyState == 4) {
			ajax_done();
			if(r.status != 200) {
				alert(r.responseText);
				return;
			}
			alert('SMS Successfuly sent to ' + f.msisdn.value);
			$('#jqpopup').dialog('destroy');
			//window.location.replace(window.location);
		}
	}
	r.send('text='+encodeURIComponent(f.message.value)+'&src='+f.src.value+'&csrfmiddlewaretoken='+getCookie('csrftoken'));	
}

function adp(id, name) {
	
	var title = id>0?'Edit District':'Add New District';
	var btns = [{text:'Submit', click:function(){ addis(id) }}];
	
	var html = '<form id="msgf"><div style="padding:30px 0px 0px 30px">\
	    <div>\
			<strong>District Name</strong>:&nbsp;&nbsp;\
			<input type="text" id="dname" maxlength="50" value="'+name+'" style="width:200px" />\
	    </div>\
	</div></form>';				
	document.getElementById('jqpopup').innerHTML = html;
	jqpopup(title, btns, 400, 200);	
};

function addis(id)
{
	var name = document.getElementById('dname').value;
	if(!(/^[a-z]{3,50}$/i.test(name))) {
		alert('District name not valid');
		return;
	}
	ajax_wait(id>0 ? 'Updating district':'Creating district ..');
	data = {name: name};
	if(id > 0) {
		data['id'] = id;
	}
	$.ajax({
			url: (id>0) ? '/districts/'+id+'/edit/' : '/districts/create/',
			cache: false,
			dataType: "json",
			type: "POST",
			data: data,
			
			error: function(data, x, error) {
					ajax_done();
					alert(error);
			},
			success: function(result) {
				ajax_done();
				if(result.error) {
					alert(result.msg); // need a show_error() function
					return;
				}
				location.replace(window.location);
			},
	});
}

function rptsetc() {
	//return; /* color coding things does not look good */;
	for(var i=0; i<reports.length; i++) {
		if(!document.getElementById('rpt_'+reports[i].id)) continue;
		var tr = (document.getElementById('rpt_'+reports[i].id).parentNode).parentNode;
		if(reports[i].closed) {
			tr.style.backgroundColor = '#F7E4E3';	
		} 
		else if(reports[i].synced) {
			tr.style.backgroundColor='#D9FBC0';
		} else if (reports[i].completed) {
			//tr.className = 'row1';
		} else {
			//tr.className = 'row2';
		}
	}
};

function create_report(id, msisdn) {
	if(!confirm('Message from '+msisdn+'. Create report?')) {
        return false;
    }
    ajax_wait('Creating report ..');
	var url = '/igreports/'+id+'/createreport/';
	var r = createHttpRequest();
	r.open('GET', url, true);

	r.onreadystatechange = function() {
		if(r.readyState == 4) {
            ajax_done();
			if(r.status != 200) {
				alert('ERR: ' + r.responseText);
			} else {
				//alert(r.responseText);
                alert('A report has been successfuly created. Reference No is: ' + r.responseText);
			}
		}
	}
	r.send(null);
}

function demo_reply() {
	document.getElementById('msg').readOnly=false;
	document.getElementById('msg').value="";
	document.getElementById('msg').focus();
}

function demo_send() {
	
	var msgf = document.getElementById('msg');
	if(msgf.readOnly) {
		return;
	}
	var idf = document.getElementById('outid');
	var senderf = document.getElementById('sender');
	var text = msgf.value;
	
	if(text.length == 0) {
		return;
	}
	
	var r = createHttpRequest();
	r.open('POST', '/demo/send/', true);
    r.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    
	r.onreadystatechange = function() {
		if(r.readyState == 4) {
			if(r.status != 200) {
				alert(r.responseText);
				return;
			} else {
				msgf.value = "Your Message has been sent";
				msgf.readOnly = true;
			}
		}
	}
	r.send('text='+encodeURIComponent(text)+'&sender='+senderf.value+'&csrfmiddlewaretoken='+getCookie('csrftoken'));
}

function demo_get() {
	var id = document.getElementById('outid').value;
	var sender = document.getElementById('sender').value;
	var url = '/demo/get/?sender=' + sender + '&id=' + id + '&t=' + (new Date().getTime());
	var r = createHttpRequest();
	r.open('GET', url, true);

	r.onreadystatechange = function() {
		if(r.readyState == 4) {
			if(r.status != 200) {
				alert('ERR: ' + r.responseText);
			} else {
				//alert(r.responseText);
				var o = eval('('+ r.responseText +')');
				var res = o.res;
				var cid = document.getElementById('outid').value;	
				if(res.id != cid) {
					document.getElementById('msg').value = res.msg;
					document.getElementById('msg').readOnly = true;

					if(cid==0 && res.id>0) {
						/* if we just loaded the page */
					}
				}
				document.getElementById('outid').value = res.id;
			}
			setTimeout(function(){demo_get()}, 2000);
		}
	}
	r.send(null);
}

function track_msg_len(f) {
	var limit = 160;
	if(f.value.length == 0) {
		document.getElementById('id_chars').value = '0 Chars';
		return;
	}
	if(f.value.length > limit) {
		f.value = (f.value).substr(0, limit);
		document.getElementById('id_chars').value = limit + ' Chars';
	}
	document.getElementById('id_chars').value = f.value.length + ' Chars';
};

function attach_counter(f) {
        var ta = document.getElementById(f);
        var p = ta.parentNode;
        var d = document.createElement('div');
        with(d.style) {
                //width = '200px';
                paddingTop='5px';
				margin='0 0 0 110px';// for django 1.3 default skin
        };
        d.innerHTML = '<input type="text" id="id_chars" class="vTextField" style="width:100px" readonly="readonly" value="' +ta.value.length + ' Chars" />';
        p.appendChild(d);
        // attach onkey(up|down) events to
        addEventHandler(ta, 'keydown', function(){ track_msg_len(ta); } );
        addEventHandler(ta, 'keyup', function(){ track_msg_len(ta); } );
};


function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
};
