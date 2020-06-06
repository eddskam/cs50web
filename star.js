changeStarColor = (event) => {
    let element = document.getElementById(avg_rating)

    let starId = parseInt(element.id)
    let strId = "";
    let i = 1
    while (i <= starId){
        strId = i.toString()
        let gold = document.getElementById(strId)
        gold.style.color = "gold"
        i++;
    }
    while (i <= 5){
        strId = i.toString()
        let white = document.getElementById(strId)
        lwhite.style.color = "white"
        i++;
    }
    this.countYellowStars()
}

countYellowStars = () => {
    debugger
    let arr = []
    let stars = document.getElementsByClassName("stars")
    for (let i = 0; i < stars.length; i++){
        if (stars[i].style.color === "gold"){
            arr.push(stars[i].style.color)
        }
    }
    this.setState({
        rating: arr.length
    })
}