var exec_id = 0;

/*function getTable(data_activities){
    var activity_cont = [];
    var acti = Object.keys(data_activities);
    for (var it = 0; it < acti.length; it ++){
        activity_cont.push([-data_activities[acti[it]], acti[it]])
    }
    activity_cont.sort();
    

}*/
function toggleExec(){
    exec_id = 1-exec_id;
    if (exec_id == 0){
        $("#toggleExec").attr('value', 'View exec');
        $("#title").text('Stats all augmented programs');
            $(".row_normal").show();
    } 
    else {
            $("#toggleExec").attr('value', 'View all');
            $("#title").text('Stats executable augmented programs');
            $(".row_normal").hide();
    }  
    updateTable();
}
function obtainProg(prog_lines, indices){
    prog_str = '<table>';
    var indices_bin = []
    for (var l=0; l<prog_lines.length; l++) indices_bin.push(0);
    for (var id=0; id< indices.length; id++) indices_bin[indices[id]] = 1;
    for (var j = 0; j < prog_lines.length; j++){
        prog_str += '<tr><td>';
        if (indices_bin[j] == 1){
            prog_str += '<span style="color: green  "> '+ prog_lines[j].replace(/</g,"&lt;").replace(/>/g,"&gt;") +' </span>'
        }
        else {
        prog_str += '<span> '+ prog_lines[j].replace(/</g,"&lt;").replace(/>/g,"&gt;") +' </span>'
        }
        prog_str += '</tr></td>';
    }
    prog_str += '</table>';
    return prog_str;
}
function obtainPreconds(conds){
    var str_func = '<ul>';
    console.log(conds)
    for (var it = 0; it < conds.length; it += 1){
        keycond = Object.keys(conds[it])[0]
        str_func += '<li> '+keycond+':' + conds[it][keycond] +'</li>';
    }
    str_func += '</ul>';
    return str_func;
}
function showOriginal(it){
    var res = data[programs[it]][3];

    
}
function showStats(it, prog_type){
    var res = data[programs[it]][2][prog_type][current_display[it][prog_type]][3];
    result_html = obtainPreconds(res);
    console.log(result_html)
    if ($("#stats"+it+"_"+prog_type).is(':empty')){
        $("#stats"+it+"_"+prog_type).append(result_html);
    }
    else {
        $("#stats"+it+"_"+prog_type).empty()

    }
    
}
function displayProg(it, prog_type){
    var progs = Object.keys(data);
    var res = data[progs[it]][2][prog_type];
    
    if (res.length == 0){
        $('#cell'+it+'_'+prog_type).empty()
        $('#cell'+it+'_'+prog_type).append("No program");
        return;
    }
    var curr_program = res[current_display[it][prog_type]];
    var prog_str = obtainProg(curr_program[2], curr_program[1])
    var lcs = curr_program[0];
    var content_cell = '<h4> LCS: '+lcs+'</h4>' + prog_str;
    $('#cell'+it+'_'+prog_type).empty()
    $('#cell'+it+'_'+prog_type).append(content_cell)
    $('#cnt'+it+'_'+prog_type).empty()
    $('#cnt'+it+'_'+prog_type).append(1+current_display[it][prog_type]+'/'+res.length)

}
function firstProg(it, prog_type){
    current_display[it][prog_type] = 0;
    displayProg(it, prog_type)

}
function lastProg(it, prog_type){
    var progs = Object.keys(data);
    var res = data[progs[it]][2][prog_type].length;
    current_display[it][prog_type] = res - 1;
    displayProg(it, prog_type)

}
function prevProg(it, prog_type){
    var progs = Object.keys(data);
    var res = data[progs[it]][2][prog_type].length;
    if (current_display[it][prog_type] > 0){
        current_display[it][prog_type] -= 1;
        displayProg(it, prog_type)
    }
    
}
function nextProg(it, prog_type){
    var progs = Object.keys(data);
    var res = data[progs[it]][2][prog_type].length;
    if (current_display[it][prog_type] < res - 1){
        current_display[it][prog_type] += 1;
        displayProg(it, prog_type)
    }
}
function updateTable(){
    $("#stats").empty();
    var table_str = "<h3> Number of programs </h3><table>";
    table_str += "<tr><th> Original </th><th>Location </th><th>Affordance </th><th> Exception </th><th> All exceptions</th></th></tr>";
    table_str += "<tr><td>"+stats['all_progs']['initial'][exec_id]+"</td><td>"+stats['all_progs']['location'][exec_id]+"</td><td>"+stats['all_progs']['affordance'][exec_id]+"</td><td>"+stats['all_progs']['program_exception'][exec_id]+"</td><td>"+stats['all_progs']['total'][exec_id]+"</td></tr>"
    table_str += "<tr>";
    for (var iti = 0; iti < 5; iti++){
        var names = ['initial', 'location', 'affordance', 'program_exception', 'total']
        type_exec = '_all';
        if (exec_id == 1){
            type_exec = '_exec';
        }
        img_name = 'viz/distr_' + names[iti] + type_exec + '.png';
        table_str += '<td><img style="width:250px" src="'+img_name+'"></img></td>'
    }
    table_str += "</tr>"
    table_str += "<tr>";
    for (var iti = 0; iti < 5; iti++){
        var names = ['initial', 'location', 'affordance', 'program_exception', 'total']
        type_exec = '_all';
        if (exec_id == 1){
            type_exec = '_exec';
        }
        img_name = 'viz/len_' + names[iti] + type_exec + '.png';
        table_str += '<td><img style="width:250px" src="'+img_name+'"></img></td>'
    }
    table_str += "</tr>"
    table_str += "<tr>";
    for (var iti = 0; iti < 5; iti++){
        if (iti == 0 || iti == 4){
            table_str += '<td></td>'
        }
        else {
           var names = ['initial', 'location', 'affordance', 'program_exception', 'total']
            type_exec = '_all';
            if (exec_id == 1){
                type_exec = '_exec';
            }
            img_name = 'viz/LCS_' + names[iti] + type_exec + '.png';
            table_str += '<td><img style="width:250px" src="'+img_name+'"></img></td>' 
        }
        
    }
    table_str += "</tr>"   
    table_str += "</table>";
    $("#stats").append(table_str);
}
var current_display = [];
$( document ).ready(function() {
        programs = Object.keys(data);
        updateTable();
        for (var it = 0; it < programs.length;  it++){
            element = data[programs[it]];
            var title_str = element[0];
            prog_str = obtainProg(element[1], []);
            current_display.push({'location': 0, 'affordance':0, 'program_exception':0});

            var augment = ['location', 'affordance', 'program_exception'];
            var buttons = []
            for (var au_id = 0; au_id < augment.length; au_id++){
                if (element[2][augment[au_id]].length > 0){
                    var str1 = '<button onclick="prevProg('+it+', \''+augment[au_id]+'\')"> Prev </button>';
                    var str2 = '<button onclick="nextProg('+it+', \''+augment[au_id]+'\')"> Next </button>';
                    var str3 = '<button onclick="firstProg('+it+', \''+augment[au_id]+'\')"> First </button>'
                    var str4 = '<button onclick="lastProg('+it+', \''+augment[au_id]+'\')"> Last </button>'
                    var str5 = '<button onclick="showStats('+it+', \''+augment[au_id]+'\')"> Precond </button>'
                    var str6 = '<div id="stats'+it+'_'+augment[au_id]+'"></div>';
                    buttons.push(str1+str2+str3+str4+str5+str6)
                }
                else {
                    buttons.push('');
                }
                
            }
            class_name = 'row_normal'
            if (element[3] == true){
                class_name = 'row_exec';
            }
            $('#table_res').append(
                '<tr class="'+class_name+'"><br><br><td><h4>'+title_str+'</h4>' + prog_str + '</td>' +
                '<td><br><br><br>'+buttons[0]+'<div id="cnt'+it+'_'+0+'"></div><div id="cell'+it+'_'+augment[0]+'"></div></td>' + 
                '<td><br><br><br>'+buttons[1]+'<div id="cnt'+it+'_'+1+'"></div><div id="cell'+it+'_'+augment[1]+'"></div></td>' + 
                '<td><br><br><br>'+buttons[2]+'<div id="cnt'+it+'_'+2+'"></div><div id="cell'+it+'_'+augment[2]+'"></div></td>')
            displayProg(it, augment[0]);
            displayProg(it, augment[1]);
            displayProg(it, augment[2]);
        }  
 });
