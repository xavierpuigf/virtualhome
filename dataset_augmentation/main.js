
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
var current_display = [];
$( document ).ready(function() {
        programs = Object.keys(data);
        var table_str = "<h3> Number of programs </h3><table>";
        table_str += "<tr><th> Original </th><th> Affordance </th><th> Place </th><th> Exception </th><th> All exceptions</th></th></tr>";
        table_str += "<tr><td>"+stats['all_progs'][0]+"</td><td>"+stats['all_progs'][1]+"</td><td>"+stats['all_progs'][2]+"</td><td>"+stats['all_progs'][3]+"</td><td>"+stats['all_progs'][4]+"</td></tr>"
        table_str += "</table>";
        $("#stats").append(table_str)
        for (var it = 0; it < programs.length; it++){
            element = data[programs[it]];
            var title_str = element[0];
            prog_str = obtainProg(element[1], []);
            current_display.push([0,0,0]);
            var str1 = '<button onclick="prevProg('+it+', 0)"> Prev </button>'
            var str2 = '<button onclick="prevProg('+it+', 1)"> Prev </button>'
            var str3 = '<button onclick="prevProg('+it+', 2)"> Prev </button>'

            var str12 = '<button onclick="nextProg('+it+', 0)"> Next </button>'
            var str22 = '<button onclick="nextProg('+it+', 1)"> Next </button>'
            var str32 = '<button onclick="nextProg('+it+', 2)"> Next </button>'

            var str1f = '<button onclick="firstProg('+it+', 0)"> First </button>'
            var str2f = '<button onclick="firstProg('+it+', 1)"> First </button>'
            var str3f = '<button onclick="firstProg('+it+', 2)"> First </button>'

            var str1l = '<button onclick="lastProg('+it+', 0)"> Last </button>'
            var str2l = '<button onclick="lastProg('+it+', 1)"> Last </button>'
            var str3l = '<button onclick="lastProg('+it+', 2)"> Last </button>'
            console.log(title_str);
            $('#table_res').append(
                '<tr><br><br><td><h4>'+title_str+'</h4>' + prog_str + '</td>' +
                '<td><br><br><br>'+str1+str12+str1f+str1l+'<div id="cnt'+it+'_'+0+'"></div><div id="cell'+it+'_'+0+'"></div></td>' + 
                '<td><br><br><br>'+str2+str22+str2f+str2l+'<div id="cnt'+it+'_'+1+'"></div><div id="cell'+it+'_'+1+'"></div></td>' + 
                '<td><br><br><br>'+str3+str32+str3f+str3l+'<div id="cnt'+it+'_'+2+'"></div><div id="cell'+it+'_'+2+'"></div></td>')
            displayProg(it, 0);
            displayProg(it, 1);
            displayProg(it, 2);
        }  
 });
