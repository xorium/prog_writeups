/*
Для получения читабельных данных по данным с карточек, нужно вызвать функцию get_readable_info, где ей передать в нужном формате (см. ниже) входные данные карточек.
Пример использования:
<script>
var test_input = `
Gerona Airport,Stockholm,1,SK455,45B,3A,344
Madrid,Barcelona,3,,78A,45B
Stockholm,New York JFK,1,SK22,22,7B,
Barcelona,Gerona Airport,2,,airport bus,
`;
var info = get_readable_info(test_input);
info = info.join("<br>");
document.getElementById("output").innerHTML = info;
</script>
См. https://jsfiddle.net/76qLovd0/2/
*/

//Вспомогательная функция для облегчения операций удаления объектов из массива (обертка над Array.prototype.splice(index, 1)).
Array.prototype.remove = function(elem) {
    var index = this.indexOf(elem);
    if (index >= 0) this.splice(index, 1);
};

//Вспомогательная функция для проверки наличия элемента в массиве (обертка над Array.prototype.indexOf())).
Array.prototype.has = function(elem) {
    var index = this.indexOf(elem);
    return index >= 0;
};

//вспомогательная функция для замены всех вхождений подстроки в строку
String.prototype.replaceAll = function(search, replacement) {
    var target = this;
    return target.split(search).join(replacement);
};

/*
Входные данные подаются в CSV формате (значения разделены запятой ",", без пробелов после запятой, каждая новая строка - новая карточка).

Каждая строка должна состоять из следующих обязательных колонок:
- место отправления (город/регион, название аэропорта, вокзала и т.п.);
- место назначения (город/регион, название аэропорта, вокзала и т.п.);
- тип транспорта (обозначается числом, см. далее);
Так же далее может следовать любое количество колонок с дополнительной информацией для разных видов транспорта (для каждого нового типа будет писаться своя функция-обработчик).

Примечания:
[*] Если какая-либо необязательная колонка в карточке отсутствует, ее надо оставить пустой и поставить запятую;
[*] Если в значении поля присутствуют запятые, то их нужно экранировать обратным слешем "\";

Тип транспорта - обозначается числовым значением:
0 - другой;
1 - воздушный (самолет);
2 - наземный (маршрутное транспортное средство, такси);
3 - железнодорожный (поезд);

Дополнительные колонки входных данных для воздушного типа транспорта:
- номер рейса;
- номер посадочного шлюза;
- номер места;
- номер багажной бирки;

Дополнительные колонки входных данных для наземного типа транспорта:
- номер транспорта;
- название транспорта (автобус, такси и пр.);
- номер места;

Дополнительные колонки входных данных для железнодорожного типа транспорта:
- номер платформы;
- номер поезда;
- номер места;

Пример входных данных:
Gerona Airport,Stockholm,1,SK455,45B,3A,344
Madrid,Barcelona,3,,78A,45B
Stockholm,New York JFK,1,SK22,22,7B,
Barcelona,Gerona Airport,2,,airport bus,
*/

//Функция парсинга данных. Возвращает массив, где каждый элемент является массивом колонок.
function parse_data(input) {
    var res = Array();
    var rows = input.split("\n");
    for (var i = 0; i < rows.length; i++) {
        var item = rows[i];
        if (!item || item.replaceAll("\\,", "").split(",").length < 3) continue; //если количество колонок меньше 3, пропускаем (некорректный формат карточки). Экранированные запятые учитываются.
        item = item.replaceAll("\\,", "\n"); //т.к. символа переноса строки быть не может, то его можно использовать как временный заменитель экранированных запятых, чтобы разбить строку на столбцы и затем обратно заменить в каждом столбце его на экранированные запятые
        var columns = item.split(",");

        for (var j = 0; j < columns.length; j++) {
            columns[j] = columns[j].replaceAll("\n", ",");
        }

        columns[2] = parseInt(columns[2]);

        if (!columns[0] || !columns[1] || typeof columns[2] != "number") continue; //некорректные данные обязательных столбцов
        res.push(columns);
    }
    return res;
}

/*
Вместо операция перестановки элементов массива был выбран метод составления списка элементов, где у каждого будет ссылка не следующий и предыдущий (исключая крайние элементы списка). Ссылка на предыдущий в текущем функционале необязательна, но возможно понадобиться в будущем, при расширении функционала. Создание ссылок потребует чуть больше памяти, но сократит количество процессорного времени.
Таким образом, позже можно будет сделать обход списка по ссылкам от первого до последнего элемента.
Алгоритм сортировки построен следующим образом: имеется 2 массива - data и pending, в первом лежат все карточки, которые нужно проверить на соответствующих "соседей" из списка, во втором - карточки, которые "ищут" себе соседние элементы (элементы, идущие за и после них).
Логика алгоритма: перебираются элементы из data и для каждого перебираются элементы из pending. 
Если после проверки всех элементов из pending для текущего элемента из data не было найдено хотя бы одного из соседних элементов (элементов, которые идут до и после текущего), значит остальные соседние элементы (или оба), находятся в самом массиве data, тогда текущий элемент добавляется в pending.
В конце каждой итерации вложенного цикла для массива pending его элементы проверяются на "завершенность" - наличие всех двух соседних элементов, и в случае выполнения этого условия, они удаляются (чтобы избежать лишних итераций для остальных элементов). Аналогичная проверка происходит в конце каждой итерации для массива data.
В конце выполненция сортировки, в массиве pending остануться 2 элемента - начальный (у которого есть только сосед после) и конечный (у которого есть только сосед до), из них выбирается начальный элемент.
Ниже описана функция, реализующая этот алгоритм.
*/
function sort_data(data) {
    var pending = Array(data[0]);
    data.remove(pending[0]);
    var first_node = pending[0];

    //служебные переменные для анализа работы алгоритма
    var data_length = data.length + 1;
    var count = 0;

    for (var i = 0; i < data.length; i++) {
        var cur_item = data[i];
        for (var j = 0; j < pending.length; j++) {
            var cur_pending = pending[j];

            if (cur_item[0] == cur_pending[1]) {
                cur_pending.next = cur_item;
                cur_item.prev = cur_pending;
            } else if (cur_item[1] == cur_pending[0]) {
                cur_pending.prev = cur_item;
                cur_item.next = cur_pending;
            }
            
            if (cur_pending.next != null && cur_pending.prev != null) {
                pending.remove(cur_pending);
                j--;
            }

            if (cur_item.next != null && cur_item.prev != null) {
                data.remove(cur_item);
                i--;
                break;
            }

            count++;
        }
        if (cur_item.next == null || cur_item.prev == null && !pending.has(cur_item)) {
            pending.push(cur_item);
            data.remove(cur_item);
            i--;
        }
    }
    
    for (var j = 0; j < pending.length; j++) {
        if (pending[j].prev == null) {
            first_node = pending[j];
            break;
        }
    }

    //console.log("Nuber of iterations: " + count);

    return first_node;
}

//функция составления читаемой строки для воздушного типа транспорта
function get_air_type_string(node) {
    var from_place = node[0];
    var to_place = node[1];
    var flight_num = node[3];
    var gate_num = node[4];
    var seat_num = node[5];
    var bagage_num = node[6];

    if (!flight_num || !gate_num || !seat_num) return ""; //не заполнены все необходимые для данного типа колонки

    var res = "From " + from_place + ", take flight " + flight_num + " to " + to_place + ". Gate " + gate_num + ". Seat " + seat_num + ". ";
    if (bagage_num) res += "Baggage drop at ticket counter " + bagage_num + ".";
    else res += "Baggage will be automatically transferred from your last leg.";

    return res;
}

//функция составления читаемой строки для наземного типа транспорта
function get_usual_type_string(node) {
    var from_place = node[0];
    var to_place = node[1];
    var transport_num = node[3];
    var transport_name = node[4];
    var seat_num = node[5];

    if (!transport_num && !transport_name) return ""; //не заполнено хотя бы одно из необходимых полей
    
    if (transport_num) transport_name += " " + transport_num;

    var res = "Take the " + transport_name + " from " + from_place + " to " + to_place + ". ";
    if (seat_num) res += "Seat " + seat_num + ".";
    else res += "No seat assignment.";
    res = res.replaceAll("  ", " ");

    return res;
}

//Функция составления читаемой строки для железнодорожного вида транспорта
function get_railway_type_string(node) {
    var from_place = node[0];
    var to_place = node[1];
    var station_num = node[3];
    var train_num = node[4];
    var seat_num = node[5];

    if (!train_num || !seat_num) return "";
    
    var res = "Take train " + train_num + " from " + from_place + " to " + to_place + ". ";
    if (station_num) res += "Station " + station_num + ". ";
    res += "Seat " + seat_num + ".";

    return res; 
}

//Функция, возвращающая читаемую строку-инструкцию для каждого маршрута из карточки
function get_string(node) {
    var res = "";
    var transport_type = node[2];

    switch (transport_type) {
        case 0:
          //...
          break;
        case 1:
          res = get_air_type_string(node);
          break;
        case 2:
          res = get_usual_type_string(node);
          break;
        case 3:
          res = get_railway_type_string(node);
          break;
    }

    return res;
}

//Обход элементов списка (элементы отсортированы)
function check_nodes(node) {
    var result = Array();
    while (node) {
        console.log(node[0] + " -> " + node[1]);
        var current_string = get_string(node);
        if (!current_string) {
            node = node.next;
            continue;
        }
        result.push(current_string);
        node = node.next;
    }
    console.log(result);
    return result;
}

/*
Функция, принимающая на вход входные данные (формат см. выше), и возвращающая массив читаемых строк (одна строка соответствует одной карточке из входных данных).
Формат выходных данных:
Массив строк, каждая строка соответствует одной карточке из входных данных.
*/
function get_readable_info(input) {
    var data = parse_data(input); //парсинг данных в массив (каждый элемент массива сам является массивом колонок)
    var fnode = sort_data(data); //сортировка данных и возвращение первого элемента
    var info = check_nodes(fnode); //обход всех элементов, конвертация их информации в читаемые строки и объединение этих строк
    return info;
}
