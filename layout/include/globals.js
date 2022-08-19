function getData() {
  return $.ajax({
    dataType: 'json',
    url: '../../out/program_state.json',
    cache: false
  })
}

function FitText(target) {
  document.fonts.ready.then(() => {
    if (target == null) return
    if (target.css('font-size') == null) return
    if (target.css('width') == null) return

    let textElement = target.find('.text')

    if (textElement.text().trim().toLowerCase() == 'undefined') {
      textElement.html('')
    }

    textElement.css('transform', '')
    let scaleX = 1

    while (textElement[0].scrollWidth * scaleX > target.width() && scaleX > 0) {
      scaleX -= 0.01
      textElement.css('transform', 'scaleX(' + scaleX + ')')
    }
  })
}

function SetInnerHtml(
  element,
  html,
  force = undefined,
  fadeTime = 0.5,
  middleFunction = undefined
) {
  if (element == null) return
  if (force == false) return

  let fadeOutTime = fadeTime
  let fadeInTime = fadeTime

  if (html == null || html == undefined) html = ''

  html = String(html)

  // First run, no need of smooth fade out
  if (element.find('.text').length == 0) {
    // Put any text inside the div just so the font loading is triggered
    element.html("<div class='text'>&nbsp;</div>")
    fadeOutTime = 0
  }

  // Wait for font to load before calculating sizes
  document.fonts.ready.then(() => {
    if (
      force == true ||
      he.decode(String(element.find('.text').html()).replace(/'/g, '"')) !=
        he.decode(String(html).replace(/'/g, '"'))
    ) {
      gsap.to(element.find('.text'), {
        autoAlpha: 0,
        duration: fadeOutTime,
        onComplete: () => {
          element.find('.text').html(html)
          FitText(element)
          if (middleFunction != undefined) {
            middleFunction()
          }
          gsap.to(element.find('.text'), {
            autoAlpha: 1,
            duration: fadeInTime
          })
        }
      })
    }
  })
}

function CenterImage(element, eyesight, customZoom = 1) {
  let image = element.css('background-image')

  if (image != undefined && image.includes('url(')) {
    let img = new Image()
    img.src = image.split('url("')[1].split('")')[0]

    $(img).on('load', () => {
      if (!eyesight) {
        eyesight = {
          x: img.naturalWidth / 2,
          y: img.naturalHeight / 2
        }
      }

      zoom_x = element.innerWidth() / img.naturalWidth
      zoom_y = element.innerHeight() / img.naturalHeight

      if (zoom_x > zoom_y) {
        zoom = zoom_x
      } else {
        zoom = zoom_y
      }

      zoom *= customZoom

      let xx = 0
      let yy = 0

      xx = -eyesight.x * zoom + element.innerWidth() / 2
      console.log('xx', xx)

      let maxMoveX = Math.abs(element.innerWidth() - img.naturalWidth * zoom)
      console.log('maxMoveX', maxMoveX)

      if (xx > 0) xx = 0
      if (xx < -maxMoveX) xx = -maxMoveX

      yy = -eyesight.y * zoom + element.innerHeight() / 2
      console.log('yy', yy)

      let maxMoveY = Math.abs(element.innerHeight() - img.naturalHeight * zoom)
      console.log('maxMoveY', maxMoveY)

      if (yy > 0) yy = 0
      if (yy < -maxMoveY) yy = -maxMoveY

      console.log('zoom', zoom)

      element.css(
        'background-position',
        `
          ${xx}px
          ${yy}px
        `
      )

      element.css(
        'background-size',
        `
          ${img.naturalWidth * zoom}px
          ${img.naturalHeight * zoom}px
        `
      )

      //element.css("background-position", "initial");
      //element.css("position", "fixed");
      //element.css("width", img.naturalWidth * zoom);
      //element.css("height", img.naturalHeight * zoom);
    })
  }
}

async function FindImages(folder = '') {
  let flag = true
  let counter = 1
  const files = []

  while (flag) {
    const filename = `${folder}/${counter}.png`
    try {
      await $.get(filename)
      files.push(filename)
      counter += 1
    } catch (e) {
      flag = false
    }
  }

  return files
}
