async function get_empleados(filtro){

	var url = window.location.origin + '/get-empleados/?q=' + filtro;

	const res = await fetch(url);
 	const json = await res.json();

 	console.log(json);
}

$(document).ready(function() {
    const price = get_empleados("lu");
});