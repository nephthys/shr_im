$(function(){

    var my_tr_focus = null;
    $('.is_author_link').mouseenter(function(event)
    {
        clearTimeout(my_tr_focus);
        $(this).find('.hide_opt_focus').fadeIn('normal').show();
    })
    .mouseleave(function(event)
    {
       my_tr_focus = setTimeout(function(){ $('.is_author_link').find('.hide_opt_focus').fadeOut('fast').hide(); }, 200);
    });
    
    $("input.selected_input").select();
    
    $('a.show_form_edit_link').click(function(){
        var id_link = $(this).attr('id');
        
        if ($('#form_'+id_link).is(":hidden")) {
            $('#url_'+id_link).hide();
            $('#form_'+id_link).show();
            
        } else {
            $('#url_'+id_link).show();
            $('#form_'+id_link).hide();
        }
        
        return false;
    });
    
    $('a.link_post').click(function(){
        if ($('#post_tweet').is(":hidden")) {
            $('#post_tweet').slideDown('normal');
            $('a.link_post').addClass('link_post_selected');
        } else {
            $('#post_tweet').slideUp('fast');
            $('a.link_post').removeClass('link_post_selected');
        }
        
        return false;
    });
    
    $('input.submit_edit_form').click(function(){
        var res_link = $(this).attr('id');
        var arr = res_link.split('submit_form_');
        var id_link = $('#idl_'+res_link).val();
        var url_link = $('#url_'+res_link).val();
        
        $('#edittext_'+arr[1]).hide();
        $('#preload_'+arr[1]).append(' &nbsp; <img src="/site_media/loader.gif" alt="Please wait" /> ');
        
        $.ajax({
		    type: "POST",
			url: "/ajax/edit",
            data: {id: id_link, url_src: url_link},
			dataType: "xml",
			success: function(xml) {
                $('#preload_'+arr[1]).empty();
                $('#edittext_'+arr[1]).show();
                $('#url_edit_link_'+arr[1]).show();
                $('#form_edit_link_'+arr[1]).hide();
                
				$(xml).find('url').each(function(){
                    var title = $(this).find('title').text();
                    var description = $(this).find('description').text();
                    var domain = $(this).find('domain').text();
                    
                    if(description != '') {
                        new_description = description;
                    } else {
                        new_description = '<em>no description</em>';
                    }
                    
                    $('#src_edit_link_'+arr[1]).text($(this).find('source').text());
                    $('#title_edit_link_'+arr[1]).text(title);
                    $('#title_h1_edit_link_'+arr[1]).text(title.substr(0,75));
                    $('#domain_edit_link_'+arr[1]).html('<a href="/d/'+domain+'/">'+domain+'</a>');
                    $('#description_edit_link_'+arr[1]).html(new_description);
				});
			}
		});
        
        return false;
    });
    
    $("#selectedField").focus(function(){
        // Select input field contents
        this.select();
    });
    
    $('a.open_chart_url').click(function(){
        var res_link = $(this).attr('id');
        var arr = res_link.split('open_');
        
        $("ul.graphs li").each(function(){
            $(this).find('a').removeClass('selected');
            $('#open_'+arr[1]).addClass('selected');
        });
        
        $(".content_graph div").each(function(){
            $(this).hide();
            $('#'+arr[1]).show();
        });
        
        return false;
    });
    
    $('a.link_plus_options').click(function(){
        if ($('#more_options_hide').is(":hidden")) {
            $('#more_options').hide();
            $('#more_options_hide').slideDown('normal').show();
        } else {
            $('#more_options').slideUp('normal').show();
            $('#more_options_hide').hide();
        }
        
        return false;
    });
    
    setTimeout(function(){ $('#msg').slideUp('slow'); }, 3500);
});