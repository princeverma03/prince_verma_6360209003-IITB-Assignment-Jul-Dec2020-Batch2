from typing import Tuple, List
from loguru import logger

import cv2
import numpy as np
from PIL.Image import Image as PILImage
from PIL.ImageFont import FreeTypeFont
from tenacity import retry

from text_renderer.bg_manager import BgManager
from text_renderer.config import RenderCfg
from text_renderer.utils.draw_utils import draw_text_on_bg, transparent_img
from text_renderer.utils import utils
from text_renderer.utils.errors import PanicError
from text_renderer.utils.math_utils import PerspectiveTransform
from text_renderer.utils.bbox import BBox
from text_renderer.utils.font_text import FontText
from text_renderer.utils.types import FontColor, is_list

from PIL import Image, ImageFont, ImageDraw
from matplotlib import pyplot as plt
BBOX_OFFSET_FROM_CHAR = 0

class Render:
    def __init__(self, cfg: RenderCfg):
        self.cfg = cfg
        self.layout = cfg.layout
        if isinstance(cfg.corpus, list) and len(cfg.corpus) == 1:
            self.corpus = cfg.corpus[0]
        else:
            self.corpus = cfg.corpus

        if is_list(self.corpus) and is_list(self.cfg.corpus_effects):
            if len(self.corpus) != len(self.cfg.corpus_effects):
                raise PanicError(
                    f"corpus length({self.corpus}) is not equal to corpus_effects length({self.cfg.corpus_effects})"
                )

        if is_list(self.corpus) and (
            self.cfg.corpus_effects and not is_list(self.cfg.corpus_effects)
        ):
            raise PanicError("corpus is list, corpus_effects is not list")

        if not is_list(self.corpus) and is_list(self.cfg.corpus_effects):
            raise PanicError("corpus_effects is list, corpus is not list")

        self.bg_manager = BgManager(cfg.bg_dir, cfg.pre_load_bg_img)

    @retry
    def __call__(self, *args, **kwargs) -> Tuple[np.ndarray, str]:
        try:
            if self._should_apply_layout():
                img, text = self.gen_multi_corpus()
            else:
                img, text = self.gen_single_corpus()

            if self.cfg.render_effects is not None:
                img, _ = self.cfg.render_effects.apply_effects(
                    img, BBox.from_size(img.size)
                )

            img = img.convert("RGB")
            np_img = np.array(img)
            np_img = cv2.cvtColor(np_img, cv2.COLOR_RGB2BGR)
            np_img = self.norm(np_img)
            return np_img, text
        except Exception as e:
            logger.exception(e)
            raise e

    def lay_bbox_over_image(self, image, font_text, text_color):
        '''
        lay_bbox_over_image method lay's boxed version on a text image, characterwise.

        Arguments:
        image - PIL image.
        font_text - font_text datastructure that contains text, font etc.
        text_color - color of the text (Data augmentation)
        
        Returns:
        image - Updated image with each character having a uniform bbox
        '''
  
        font = font_text.font
        text = font_text.text
        xref, yref = font_text.xy
        
        draw = ImageDraw.Draw(image)
        overlap_flag = True

        random_num_spaces = np.random.randint(11) #assuming max 11 spaces added after the text
        text = text.ljust((len(text)+ random_num_spaces),' ')
        
        for i, c in enumerate(text):
            wd0, ht0 = font.getsize(text[:i+1])

            #Assumes that there is character spacing between each character (depends on font size and font name)
            char_wd, char_ht = font.getsize(c)
        
            x2, y2 = wd0, char_ht
            x1, y1 = x2 - char_wd, y2 - char_ht

            if i == 0:
                x1 = x1 - BBOX_OFFSET_FROM_CHAR 
            y1 = y1 - BBOX_OFFSET_FROM_CHAR 
        
            if i == (len(text)-1):
                x2 = x2 + BBOX_OFFSET_FROM_CHAR
            y2 = y2 + BBOX_OFFSET_FROM_CHAR

            #check if bbox extends down or up for characters like y, p, j etc
            if i==0:
                (x1_init, y1_init, x2_init, y2_init) = x1, y1, x2, y2
                x1_prev, y1_prev, x2_prev, y2_prev = x1, y1, x2, y2

            #Maintaining same height of the box for all characters through out the text.
            if (y1 != y1_init):
                y1 = y1_init
        
            if (y2 != y2_init):
                y2 = y2_init

            #check if two two adjacent bbox of characters are overlapping
            if i >= 1:
                if (x1_prev >= x2 or x1 >= x2_prev):
                    overlap_flag = False
                    
                if (y1_prev <= y2 or y1 <= y2_prev):
                    overlap_flag = False
                    
                if (overlap_flag):
                    x1 = (x2_prev - x1_prev)
                    y1 = y1_prev    
    
                x1_prev, y1_prev, x2_prev, y2_prev = x1, y1, x2, y2

            #check if two ajacent boxes have considerable width.(5pixels)
            if (x2 - x1 < 5):
                x2, y2 = x2_prev, y2_prev
   
            draw.rectangle((x1 + xref, y1 + yref, x2 + xref, y2 + yref), fill=None, outline='black', width=1)
            
        return image


    def gen_single_corpus(self) -> Tuple[PILImage, str]:
        font_text = self.corpus.sample()

        bg = self.bg_manager.get_bg()
        text_color = self.corpus.cfg.text_color_cfg.get_color(bg)
        text_mask = draw_text_on_bg(
            font_text, text_color, char_spacing=self.corpus.cfg.char_spacing
        )

        if self.cfg.corpus_effects is not None:
            text_mask, _ = self.cfg.corpus_effects.apply_effects(
                text_mask, BBox.from_size(text_mask.size)
            )

        if self.cfg.perspective_transform is not None:
            transformer = PerspectiveTransform(self.cfg.perspective_transform)
            # TODO: refactor this, now we must call get_transformed_size to call gen_warp_matrix
            _ = transformer.get_transformed_size(text_mask.size)

            try:
                (
                    transformed_text_mask,
                    transformed_text_pnts,
                ) = transformer.do_warp_perspective(text_mask)
            except Exception as e:
                logger.exception(e)
                logger.error(font_text.font_path, "text", font_text.text)
                raise e
        else:
            transformed_text_mask = text_mask

        
        img = self.paste_text_mask_on_bg(bg, transformed_text_mask)

        # After pasting the text mask on the background we draw bbox for each character on the transformed image. 
        img = self.lay_bbox_over_image(image= img, font_text= font_text, text_color= text_color)
        
        return img, font_text.text

    def gen_multi_corpus(self) -> Tuple[PILImage, str]:
        font_texts: List[FontText] = [it.sample() for it in self.corpus]

        bg = self.bg_manager.get_bg()

        text_color = None
        if self.cfg.text_color_cfg is not None:
            text_color = self.cfg.text_color_cfg.get_color(bg)

        text_masks, text_bboxes = [], []
        for i in range(len(font_texts)):
            font_text = font_texts[i]

            if text_color is None:
                _text_color = self.corpus[i].cfg.text_color_cfg.get_color(bg)
            else:
                _text_color = text_color
            text_mask = draw_text_on_bg(
                font_text, _text_color, char_spacing=self.corpus[i].cfg.char_spacing
            )

            text_bbox = BBox.from_size(text_mask.size)
            if self.cfg.corpus_effects is not None:
                effects = self.cfg.corpus_effects[i]
                if effects is not None:
                    text_mask, text_bbox = effects.apply_effects(text_mask, text_bbox)
            text_masks.append(text_mask)
            text_bboxes.append(text_bbox)

        text_mask_bboxes, merged_text = self.layout(
            font_texts,
            [it.copy() for it in text_bboxes],
            [BBox.from_size(it.size) for it in text_masks],
        )
        if len(text_mask_bboxes) != len(text_bboxes):
            raise PanicError(
                "points and text_bboxes should have same length after layout output"
            )

        merged_bbox = BBox.from_bboxes(text_mask_bboxes)
        merged_text_mask = transparent_img(merged_bbox.size)
        for text_mask, bbox in zip(text_masks, text_mask_bboxes):
            merged_text_mask.paste(text_mask, bbox.left_top)

        if self.cfg.perspective_transform is not None:
            transformer = PerspectiveTransform(self.cfg.perspective_transform)
            # TODO: refactor this, now we must call get_transformed_size to call gen_warp_matrix
            _ = transformer.get_transformed_size(merged_text_mask.size)

            (
                transformed_text_mask,
                transformed_text_pnts,
            ) = transformer.do_warp_perspective(merged_text_mask)
        else:
            transformed_text_mask = merged_text_mask

        if self.cfg.layout_effects is not None:
            transformed_text_mask, _ = self.cfg.layout_effects.apply_effects(
                transformed_text_mask, BBox.from_size(transformed_text_mask.size)
            )

        img = self.paste_text_mask_on_bg(bg, transformed_text_mask)
        
        return img, merged_text

    def paste_text_mask_on_bg(
        self, bg: PILImage, transformed_text_mask: PILImage
    ) -> PILImage:
        """

        Args:
            bg:
            transformed_text_mask:

        Returns:

        """
        x_offset, y_offset = utils.random_xy_offset(transformed_text_mask.size, bg.size)
        bg = self.bg_manager.guard_bg_size(bg, transformed_text_mask.size)
        bg = bg.crop(
            (
                x_offset,
                y_offset,
                x_offset + transformed_text_mask.width,
                y_offset + transformed_text_mask.height,
            )
        )
        bg.paste(transformed_text_mask, (0, 0), mask=transformed_text_mask)
        return bg

    def get_text_color(self, bg: PILImage, text: str, font: FreeTypeFont) -> FontColor:
        # TODO: better get text color
        # text_mask = self.draw_text_on_transparent_bg(text, font)
        np_img = np.array(bg)
        # mean = np.mean(np_img, axis=2)
        mean = np.mean(np_img)

        alpha = np.random.randint(110, 255)
        r = np.random.randint(0, int(mean * 0.7))
        g = np.random.randint(0, int(mean * 0.7))
        b = np.random.randint(0, int(mean * 0.7))
        fg_text_color = (r, g, b, alpha)

        return fg_text_color

    def _should_apply_layout(self) -> bool:
        return isinstance(self.corpus, list) and len(self.corpus) > 1

    def norm(self, image: np.ndarray) -> np.ndarray:
        if self.cfg.gray:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if self.cfg.height != -1 and self.cfg.height != image.shape[0]:
            height, width = image.shape[:2]
            width = int(width // (height / self.cfg.height))
            image = cv2.resize(
                image, (width, self.cfg.height), interpolation=cv2.INTER_CUBIC
            )

        return image
